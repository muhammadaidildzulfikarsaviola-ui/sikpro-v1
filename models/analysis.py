class Analysis:

    def __init__(
        self,
        analysis_type,
        title,
        data,
        stats,
        settings,
        navigator_name=""
    ):

        self.analysis_type = analysis_type

        self.title = title

        self.data = data

        self.stats = stats

        self.settings = settings

        self.navigator_name = navigator_name

    def to_dict(self):

        return {

            "analysis_type": self.analysis_type,

            "title": self.title,

            "data": self.data,

            "stats": self.stats,

            "settings": self.settings,

            "navigator_name": self.navigator_name
        }