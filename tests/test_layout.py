import json
import tempfile
import unittest
from pathlib import Path

from layout.algorithm import (closeness_score, generate_alternatives,
                              material_flow_distance, shared_boundary,
                              validate_geometry)
from layout.export import export_pdf, export_png
from layout.models import LayoutProject, Rectangle, relation_key
from layout.persistence import FORMAT_NAME, FORMAT_VERSION, load_project, save_project
from layout.visualization import canvas_to_world, fit_department_label, fit_floor_view
from unittest.mock import patch


def sample_project():
    project = LayoutProject("Training Factory", 20, 12)
    first = project.add_department("Cutting", 40)
    second = project.add_department("Assembly", 35)
    third = project.add_department("Inspection", 25)
    project.set_relationship(first.id, second.id, "A", "Shared production flow")
    project.set_relationship(first.id, third.id, "X", "Keep noise away")
    project.set_relationship(second.id, third.id, "E")
    project.set_material_flow(first.id, second.id, 12)
    return project


class LayoutRelationshipTests(unittest.TestCase):
    def test_pairs_are_canonical_symmetric_and_department_crud_updates_matrix(self):
        project = LayoutProject("Test", 10, 10)
        first = project.add_department("Cutting", 20)
        second = project.add_department("Assembly", 20)
        third = project.add_department("Inspection", 20)
        self.assertEqual(set(project.relationships), {
            relation_key(first.id, second.id), relation_key(first.id, third.id),
            relation_key(second.id, third.id),
        })
        project.set_relationship(second.id, first.id, "E", "Near flow")
        self.assertEqual(project.relationships[relation_key(first.id, second.id)].rating, "E")
        self.assertEqual(project.relationships[relation_key(second.id, first.id)].reason, "Near flow")
        project.remove_department(second.id)
        self.assertTrue(all(second.id not in pair for pair in project.relationships))

    def test_all_ratings_are_supported_and_incomplete_matrix_blocks_generation(self):
        project = LayoutProject("Test", 10, 10)
        departments = [project.add_department(name, 10) for name in ("A", "B", "C")]
        for (first, second), rating in zip(
            ((departments[0], departments[1]), (departments[0], departments[2]),
             (departments[1], departments[2])), ("A", "E", "X")
        ):
            project.set_relationship(first.id, second.id, rating)
        self.assertEqual(project.input_errors(), [])
        project.remove_relationship(departments[0].id, departments[1].id)
        self.assertTrue(any(error.startswith("relationship_missing") for error in project.input_errors()))
        with self.assertRaises(ValueError):
            generate_alternatives(project)
        with self.assertRaises(ValueError):
            project.set_relationship(departments[0].id, departments[1].id, "Z")

    def test_contradictory_reverse_duplicate_is_rejected_on_load(self):
        project = sample_project().to_dict()
        reverse = dict(project["relationships"][0])
        reverse["first"], reverse["second"] = reverse["second"], reverse["first"]
        project["relationships"].append(reverse)
        with self.assertRaises(ValueError):
            LayoutProject.from_dict(project)


class LayoutAlgorithmTests(unittest.TestCase):
    def test_shared_boundary_closeness_score_and_x_penalty(self):
        project = LayoutProject("Test", 10, 5)
        a = project.add_department("A", 10)
        b = project.add_department("B", 10)
        project.set_relationship(a.id, b.id, "X")
        adjacent = {a.id: Rectangle(0, 0, 2, 5), b.id: Rectangle(2, 0, 2, 5)}
        separate = {a.id: Rectangle(0, 0, 2, 5), b.id: Rectangle(4, 0, 2, 5)}
        self.assertEqual(shared_boundary(adjacent[a.id], adjacent[b.id]), 5)
        self.assertEqual(closeness_score(project, adjacent), -project.x_penalty * 5)
        self.assertEqual(closeness_score(project, separate), 0)

    def test_generation_is_deterministic_preserves_area_bounds_and_no_overlap(self):
        project = sample_project()
        first = generate_alternatives(project, limit=6)
        first_state = [item.to_dict() for item in first]
        second = generate_alternatives(project, limit=6)
        self.assertEqual(first_state, [item.to_dict() for item in second])
        self.assertGreater(len(first), 1)
        for alternative in first:
            self.assertTrue(alternative.is_valid, alternative.geometry_errors)
            self.assertEqual(validate_geometry(project, alternative), [])
            self.assertAlmostEqual(alternative.score,
                                   closeness_score(project, alternative.rectangles))
            for department in project.departments:
                self.assertAlmostEqual(alternative.rectangles[department.id].area, department.required_area)
        self.assertIsNotNone(first[0].flow_distance)
        self.assertEqual(first[0].flow_distance,
                         material_flow_distance(project, first[0].rectangles))

    def test_alternatives_have_distinct_rectangle_geometries(self):
        project = sample_project()
        alternatives = generate_alternatives(project, limit=6)
        self.assertGreater(len(alternatives), 1)
        signatures = {
            tuple((department_id, rectangle.x, rectangle.y, rectangle.width, rectangle.height)
                  for department_id, rectangle in sorted(alternative.rectangles.items()))
            for alternative in alternatives
        }
        self.assertEqual(len(signatures), len(alternatives))
        self.assertTrue(any(
            (first.rectangles[item].width, first.rectangles[item].height)
            != (second.rectangles[item].width, second.rectangles[item].height)
            for index, first in enumerate(alternatives)
            for second in alternatives[index + 1:]
            for item in first.rectangles
        ), "alternatives should change block geometry, not only display labels")
    def test_missing_flow_data_does_not_create_a_distance_metric(self):
        project = sample_project()
        project.material_flows.clear()
        alternative = generate_alternatives(project)[0]
        self.assertIsNone(alternative.flow_distance)

    def test_overlap_boundary_and_area_errors_are_reported(self):
        project = LayoutProject("Test", 10, 10)
        first = project.add_department("A", 20)
        second = project.add_department("B", 20)
        project.set_relationship(first.id, second.id, "O")
        layout = type("Alternative", (), {"rectangles": {
            first.id: Rectangle(0, 0, 5, 4),
            second.id: Rectangle(4, 0, 7, 4),
        }})()
        errors = validate_geometry(project, layout)
        self.assertTrue(any(error.startswith("geometry_overlap") for error in errors))
        self.assertTrue(any(error.startswith("geometry_bounds") for error in errors))
        self.assertTrue(any(error.startswith("geometry_area") for error in errors))

    def test_input_validation_rejects_excess_area_and_bad_dimensions(self):
        project = LayoutProject("Test", 5, 5)
        project.add_department("A", 30, 4, None)
        project.add_department("a", 5)
        errors = project.input_errors(require_complete_relationships=False)
        self.assertIn("department_dimensions_pair:D01", errors)
        self.assertIn("department_names_unique", errors)
        self.assertIn("required_area_exceeds_floor", errors)


class LayoutVisualizationTests(unittest.TestCase):
    def test_floor_fit_preserves_aspect_and_centers_in_available_canvas(self):
        view = fit_floor_view(900, 600, 40, 30, padding=34)
        self.assertAlmostEqual(view["width"] / view["height"], 40 / 30)
        self.assertAlmostEqual(view["origin_x"], (900 - view["width"]) / 2)
        self.assertAlmostEqual(view["origin_y"], (600 - view["height"]) / 2)
        world = canvas_to_world(view["origin_x"] + 10 * view["scale"],
                                view["origin_y"] + 8 * view["scale"], 30, view)
        self.assertAlmostEqual(world[0], 10)
        self.assertAlmostEqual(world[1], 22)

    def test_labels_shrink_or_fall_back_without_exceeding_small_blocks(self):
        full = fit_department_label("D01", "Cutting", 42, 180, 100)
        compact = fit_department_label("D01", "A very long department name", 42, 60, 24)
        absent = fit_department_label("D01", "A very long department name", 42, 5, 5)
        self.assertIn("Cutting", full[0])
        self.assertEqual(compact[0], "D01")
        self.assertIsNone(absent)


class LayoutPersistenceAndExportTests(unittest.TestCase):
    def test_round_trip_preserves_relationships_flows_alternatives_and_settings(self):
        project = sample_project()
        project.scoring_weights["A"] = 8.5
        project.x_penalty = 24.0
        generate_alternatives(project)
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as directory:
            path = Path(directory) / "training.layoutproj"
            save_project(path, project)
            restored = load_project(path)
        self.assertEqual(restored.to_dict(), project.to_dict())

    def test_unsupported_version_and_malformed_file_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.layoutproj"
            path.write_text(json.dumps({"format": FORMAT_NAME, "version": FORMAT_VERSION + 1,
                                        "project": sample_project().to_dict()}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unsupported Layout project version"):
                load_project(path)
            path.write_text("{bad json", encoding="utf-8")
            with self.assertRaises(json.JSONDecodeError):
                load_project(path)

    def test_failed_atomic_replace_preserves_existing_project_file(self):
        project = sample_project()
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as directory:
            path = Path(directory) / "training.layoutproj"
            original = b"previous valid project contents"
            path.write_bytes(original)
            with patch("layout.persistence.os.replace", side_effect=OSError("simulated replace failure")):
                with self.assertRaisesRegex(OSError, "simulated replace failure"):
                    save_project(path, project)
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(list(Path(directory).glob("*.tmp")), [])

    def test_png_and_pdf_exports_are_created_and_identify_layout(self):
        project = sample_project()
        generate_alternatives(project)
        with tempfile.TemporaryDirectory() as directory:
            png_path = Path(directory) / "layout.png"
            pdf_path = Path(directory) / "layout.pdf"
            export_png(png_path, project, project.alternatives[0], language="id")
            export_pdf(pdf_path, project, language="id")
            self.assertEqual(png_path.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
            self.assertTrue(png_path.stat().st_size > 2_000)
            self.assertEqual(pdf_path.read_bytes()[:5], b"%PDF-")
            self.assertTrue(pdf_path.stat().st_size > 2_000)


if __name__ == "__main__":
    unittest.main()
