class AffixIONeMoError(RuntimeError):
    pass


class AffixIOConfigurationError(AffixIONeMoError):
    pass


class AffixIOApiError(AffixIONeMoError):
    def __init__(self, message: str, *, status_code: int | None = None, response: object | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class AffixIOToolBlocked(AffixIONeMoError):
    def __init__(self, decision: object):
        self.decision = decision
        super().__init__("AffixIO blocked the NeMo tool call")
