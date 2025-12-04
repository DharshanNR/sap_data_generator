class ValidationResult:
    def __init__(self, category,check_name, status, severity, description, violations=0, affected_percentage=0.0, examples=None):
        self.check_name = check_name
        self.category=category
        self.status = status # "PASS", "FAIL", "WARNING"
        self.severity = severity # "Critical", "Warning", "Info"
        self.description = description
        self.violations = violations
        self.affected_percentage = affected_percentage
        self.examples = examples if examples is not None else []

    def to_dict(self):
        return {
            "category" : self.category,
            "check_name": self.check_name,
            "status": self.status,
            "severity": self.severity,
            "description": self.description,
            "violations": self.violations,
            "affected_percentage": round(self.affected_percentage, 2),
            "examples": self.examples
        }