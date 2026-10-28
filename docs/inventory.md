# SIKPRO Finished-Goods Inventory

Inventory data is stored separately from SPC `.spcproj` files and Layout `.layoutproj` files.

## Data location and initialization

- Windows: `%APPDATA%\SIKPRO\inventory.json`
- Other platforms: `~/.config/SIKPRO/inventory.json`
- The first Inventory launch creates an empty version 1 data file if none exists.
- Language and theme remain in the existing `settings.json`; changing them does not change inventory data.

## Stored data

The JSON envelope identifies the `sikpro-inventory` format and schema version. Its data contains:

- Item master records, including opening stock and minimum-stock threshold.
- Stock-in and stock-out transactions with item, quantity, timestamp, reference, and notes.
- Physical stocktakes with the recorded system balance, count, calculated variance, timestamp, and notes.
- Explicit adjustments linked to a stocktake, with the signed quantity and required audit reason.
- A monotonically increasing ledger sequence so same-time events replay in their actual order.

Current recorded balance is derived as opening stock + stock-in − stock-out + adjustments. Ordinary edits to an item never change that balance. A physical count alone never changes it either.

Each accepted change is written using a same-folder temporary file and atomic replacement before the in-memory inventory is updated. A failed replacement keeps the previous file and active balance. Unsupported or malformed files are rejected without replacing them.

## Backups

Close SIKPRO before making a backup, then copy `inventory.json` to a separate protected location. Keep multiple dated copies if the inventory is important. Do not edit the JSON manually; malformed or inconsistent ledgers are rejected on next launch. Restoring a backup replaces only Inventory data and does not affect SPC projects, Layout projects, language, or theme.
