# Error Handling

FastOpenAPI automatically handles validation errors through Pydantic.

### Customizing Errors

```python
try:
    # some validation logic
except ValidationError as exc:
    # custom handling
```

---

[<< Back](index.md)