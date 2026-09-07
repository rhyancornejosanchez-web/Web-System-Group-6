class LoginForm:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.errors = []

    def validate(self):
        if not self.username or not self.password:
            self.errors.append("Username and password are required.")
            return False
        return True


class MessageForm:
    def __init__(self, subject, body):
        self.subject = subject
        self.body = body
        self.errors = []

    def validate(self):
        if not self.subject or not self.body:
            self.errors.append("Subject and message body are required.")
            return False
        return True


class UnitForm:
    def __init__(self, data):
        self.unit_number = data.get('unit_number', '').strip()
        self.floor = data.get('floor', '')
        self.unit_type = data.get('unit_type', '').strip()
        self.monthly_rent = data.get('monthly_rent', '')
        self.description = data.get('description', '').strip()
        self.amenities = data.get('amenities', '').strip()
        self.errors = []

    def validate(self):
        if not self.unit_number:
            self.errors.append("Unit number is required.")
        if not self.floor:
            self.errors.append("Floor is required.")
        if not self.unit_type:
            self.errors.append("Unit type is required.")
        if not self.monthly_rent:
            self.errors.append("Monthly rent is required.")
        try:
            float(self.monthly_rent)
            int(self.floor)
        except (ValueError, TypeError):
            self.errors.append("Rent and floor must be valid numbers.")
        return len(self.errors) == 0