# Validation

This guide covers data validation using Pydantic models in FastOpenAPI.

## Pydantic Basics

FastOpenAPI uses Pydantic v2 for validation. All request bodies and response models are Pydantic models.

### Basic Model

```python
from pydantic import BaseModel

class User(BaseModel):
    name: str
    email: str
    age: int
```

### Type Validation

Pydantic automatically validates types:

```python
# Valid
User(name="John", email="john@example.com", age=25)

# Invalid - age must be int
User(name="John", email="john@example.com", age="25")  # Converts to int

# Invalid - missing field
User(name="John", email="john@example.com")  # ValidationError
```

## Field Constraints

Use `Field` to add validation rules:

```python
from pydantic import BaseModel, Field

class Item(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0, description="Price must be positive")
    quantity: int = Field(1, ge=0, le=10000)
    description: str | None = Field(None, max_length=500)
```

### String Constraints

```python
from pydantic import Field

class Product(BaseModel):
    name: str = Field(..., min_length=3, max_length=50)
    sku: str = Field(..., pattern=r'^[A-Z]{3}-\d{6}$')
    description: str = Field(None, max_length=1000)
```

**Available constraints:**

- `min_length` - Minimum string length
- `max_length` - Maximum string length
- `pattern` - Regex pattern (string must match)
- `strip_whitespace` - Remove leading/trailing whitespace

### Numeric Constraints

```python
class PriceRange(BaseModel):
    min_price: float = Field(..., ge=0, description="Minimum price")
    max_price: float = Field(..., gt=0, le=1000000)
    discount: float = Field(0, ge=0, le=1, description="0 to 1")
```

**Available constraints:**

- `gt` - Greater than
- `ge` - Greater than or equal to
- `lt` - Less than
- `le` - Less than or equal to
- `multiple_of` - Must be multiple of value

### Collection Constraints

```python
class ItemList(BaseModel):
    tags: list[str] = Field(..., min_length=1, max_length=10)
    categories: set[str] = Field(default_factory=set, max_length=5)
```

## Default Values

### Simple Defaults

```python
class User(BaseModel):
    name: str
    email: str
    age: int = 18  # Default value
    is_active: bool = True
```

### Default Factories

Use `default_factory` for mutable defaults:

```python
class Order(BaseModel):
    items: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
```

### Optional Fields

```python
class User(BaseModel):
    name: str
    email: str
    phone: str | None = None  # Optional field
    address: str | None = None
```

## Custom Validators

### Field Validator

Validate individual fields:

```python
from pydantic import field_validator

class User(BaseModel):
    username: str
    email: str
    
    @field_validator('username')
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        if not v.isalnum():
            raise ValueError('Username must be alphanumeric')
        return v.lower()  # Normalize to lowercase
    
    @field_validator('email')
    @classmethod
    def email_valid(cls, v: str) -> str:
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v.lower()
```

### Multiple Field Validator

Validate multiple fields with one validator:

```python
class Password(BaseModel):
    password: str
    confirm_password: str
    
    @field_validator('password')
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain digit')
        return v
```

### Model Validator

Validate relationships between fields:

```python
from pydantic import model_validator

class DateRange(BaseModel):
    start_date: date
    end_date: date
    
    @model_validator(mode='after')
    def validate_dates(self):
        if self.start_date > self.end_date:
            raise ValueError('start_date must be before end_date')
        return self
```

### Before/After Validation

```python
class Item(BaseModel):
    name: str
    price: float
    
    @field_validator('name', mode='before')
    @classmethod
    def strip_name(cls, v):
        # Runs before type validation
        if isinstance(v, str):
            return v.strip()
        return v
    
    @field_validator('price', mode='after')
    @classmethod
    def round_price(cls, v: float) -> float:
        # Runs after type validation
        return round(v, 2)
```

## Built-in Types

Pydantic provides many built-in validated types:

### Email

```python
from pydantic import EmailStr

class User(BaseModel):
    email: EmailStr  # Validates email format
```

### URLs

```python
from pydantic import HttpUrl, AnyUrl

class Link(BaseModel):
    website: HttpUrl  # Must be valid HTTP/HTTPS URL
    homepage: AnyUrl  # Any URL scheme
```

### UUIDs

```python
from uuid import UUID

class Resource(BaseModel):
    id: UUID  # Validates UUID format
```

### Dates and Times

```python
from datetime import date, datetime, time

class Event(BaseModel):
    event_date: date
    event_time: time
    created_at: datetime
```

### JSON

```python
from pydantic import Json

class Config(BaseModel):
    settings: Json  # Parses JSON string to dict
```

### Strict Types

```python
from pydantic import StrictInt, StrictStr, StrictBool

class StrictData(BaseModel):
    id: StrictInt  # Won't convert from string
    name: StrictStr  # Won't convert from other types
    active: StrictBool  # Won't convert from int
```

## Enums

Use enums for fixed choices:

```python
from enum import Enum

class Status(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class Order(BaseModel):
    id: int
    status: Status  # Must be one of the enum values
```

**Usage:**

```python
# Valid
Order(id=1, status="pending")
Order(id=1, status=Status.PENDING)

# Invalid
Order(id=1, status="unknown")  # ValidationError
```

## Nested Models

Validate nested data structures:

```python
class Address(BaseModel):
    street: str
    city: str
    postal_code: str
    country: str = "USA"

class User(BaseModel):
    name: str
    email: EmailStr
    address: Address  # Nested model

# Usage
user = User(
    name="John",
    email="john@example.com",
    address={
        "street": "123 Main St",
        "city": "New York",
        "postal_code": "10001"
    }
)
```

### Lists of Nested Models

```python
class Item(BaseModel):
    name: str
    price: float

class Order(BaseModel):
    order_id: int
    items: list[Item]  # List of nested models
    total: float
```

### Deeply Nested Models

```python
class LineItem(BaseModel):
    product_id: int
    quantity: int
    price: float

class ShippingAddress(BaseModel):
    street: str
    city: str
    country: str

class Order(BaseModel):
    order_id: int
    items: list[LineItem]
    shipping_address: ShippingAddress
    created_at: datetime
```

## Validation Modes

### Strict Mode

Disable type coercion:

```python
from pydantic import ConfigDict

class StrictUser(BaseModel):
    model_config = ConfigDict(strict=True)
    
    id: int  # Won't convert "123" to 123
    name: str  # Won't convert 123 to "123"
```

### Extra Fields

Control behavior with extra fields:

```python
class User(BaseModel):
    model_config = ConfigDict(extra='forbid')  # Reject extra fields
    
    name: str
    email: str

# This will raise ValidationError
User(name="John", email="john@example.com", age=25)  # age not allowed
```

**Options:**

- `extra='allow'` - Allow and include extra fields
- `extra='ignore'` - Allow but ignore extra fields
- `extra='forbid'` - Reject extra fields (validation error)

## Alias and Serialization

### Field Aliases

Use different names in JSON vs Python:

```python
class User(BaseModel):
    name: str = Field(..., alias='fullName')
    email: str = Field(..., alias='emailAddress')
```

**Request:**
```json
{
  "fullName": "John Doe",
  "emailAddress": "john@example.com"
}
```

**Python:**
```python
user.name  # "John Doe"
user.email  # "john@example.com"
```

### Serialization Aliases

Different alias for serialization:

```python
class User(BaseModel):
    internal_id: int = Field(..., alias='userId', serialization_alias='id')
```

**Request uses `userId`, response uses `id`**

## Complex Validation Examples

### Password Validation

```python
import re
from pydantic import field_validator

class PasswordCreate(BaseModel):
    password: str
    confirm_password: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain special character')
        return v
    
    @model_validator(mode='after')
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError('Passwords do not match')
        return self
```

### Phone Number Validation

```python
class Contact(BaseModel):
    phone: str
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        # Remove non-digits
        digits = re.sub(r'\D', '', v)
        
        if len(digits) != 10:
            raise ValueError('Phone number must be 10 digits')
        
        # Format as (XXX) XXX-XXXX
        return f'({digits[:3]}) {digits[3:6]}-{digits[6:]}'
```

### Credit Card Validation

```python
class Payment(BaseModel):
    card_number: str
    cvv: str
    expiry_month: int
    expiry_year: int
    
    @field_validator('card_number')
    @classmethod
    def validate_card(cls, v: str) -> str:
        digits = v.replace(' ', '').replace('-', '')
        
        if not digits.isdigit():
            raise ValueError('Card number must contain only digits')
        
        if len(digits) not in [13, 14, 15, 16]:
            raise ValueError('Invalid card number length')
        
        # Luhn algorithm
        total = 0
        reverse_digits = digits[::-1]
        for i, digit in enumerate(reverse_digits):
            n = int(digit)
            if i % 2 == 1:
                n *= 2
                if n > 9:
                    n -= 9
            total += n
        
        if total % 10 != 0:
            raise ValueError('Invalid card number')
        
        return digits
    
    @field_validator('cvv')
    @classmethod
    def validate_cvv(cls, v: str) -> str:
        if not v.isdigit() or len(v) not in [3, 4]:
            raise ValueError('CVV must be 3 or 4 digits')
        return v
    
    @model_validator(mode='after')
    def validate_expiry(self):
        if not (1 <= self.expiry_month <= 12):
            raise ValueError('Invalid expiry month')
        
        current_year = datetime.now().year
        if self.expiry_year < current_year:
            raise ValueError('Card has expired')
        
        if self.expiry_year == current_year:
            current_month = datetime.now().month
            if self.expiry_month < current_month:
                raise ValueError('Card has expired')
        
        return self
```

## Validation Error Format

When validation fails, FastOpenAPI returns a standardized error:

```json
{
  "error": {
    "type": "validation_error",
    "message": "Validation error",
    "status": 422,
    "details": [
      {
        "loc": ["body", "price"],
        "msg": "Input should be greater than 0",
        "type": "greater_than",
        "input": -10
      }
    ]
  }
}
```

## Custom Error Messages

Provide custom error messages:

```python
class Item(BaseModel):
    name: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Item name",
        json_schema_extra={
            "examples": ["Laptop", "Phone"]
        }
    )
    price: float = Field(
        ...,
        gt=0,
        description="Price must be positive"
    )
```

## Performance Tips

### Use Strict Mode Selectively

```python
# Only strict for critical fields
class Transaction(BaseModel):
    amount: StrictFloat  # No coercion for money
    description: str     # Coercion ok
```

### Reuse Models

```python
# Don't create new models unnecessarily
UserBase = ...  # Define once
UserCreate = UserBase  # Reuse
UserUpdate = UserBase  # Reuse
```

### Lazy Validation

```python
# Validate only when needed
class User(BaseModel):
    model_config = ConfigDict(validate_assignment=False)
    
    name: str
    email: str

# Validation happens only on creation
user = User(name="John", email="john@example.com")
user.email = "invalid"  # Not validated immediately
```

## Best Practices

### 1. Use Field Descriptions

```python
# Good
name: str = Field(..., description="User's full name")

# Avoid
name: str
```

### 2. Provide Examples

```python
# Good
email: EmailStr = Field(
    ...,
    description="User email",
    examples=["user@example.com"]
)
```

### 3. Use Meaningful Error Messages

```python
@field_validator('age')
@classmethod
def validate_age(cls, v: int) -> int:
    if v < 18:
        raise ValueError('Must be 18 or older to register')
    return v
```

### 4. Separate Create/Update Models

```python
# Create - all required
class ItemCreate(BaseModel):
    name: str
    price: float

# Update - all optional
class ItemUpdate(BaseModel):
    name: str | None = None
    price: float | None = None
```

### 5. Use Type Hints Consistently

```python
# Good
items: list[str]
metadata: dict[str, Any]

# Avoid
items: list
metadata: dict
```

## Next Steps

- [Error Handling](error_handling.md) - Handle validation errors
- [Request Body](request_body.md) - Use validation in requests
- [Response Handling](response_handling.md) - Validate responses
- [Dependencies](dependencies.md) - Validate dependency returns
