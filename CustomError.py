class Error(Exception):
    """Base class for other exceptions."""

    pass


class HomeworkNameError(Error):
    """HomeworkNameError exceptions."""

    pass


class HomeworkStatusError(Error):
    """HomeworkStatusError exceptions."""

    pass


class HomeworkVerdictError(Error):
    """HomeworkVerdictError exceptions."""

    pass


class TypeHomeworkError(Error):
    """TypeHomeworkError exceptions."""

    pass


class ListHomeworkEmptyError(Error):
    """ListHomeworkEmptyError exceptions."""

    pass
