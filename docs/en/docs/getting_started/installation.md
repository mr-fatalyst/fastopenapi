# Installation

FastOpenAPI is available on PyPI and supports **Python 3.10+**. You can install the core library or include optional dependencies for specific web frameworks. 

## Prerequisites

- **Python 3.10 or higher** – FastOpenAPI requires Python 3.10+ due to its use of modern typing features and Pydantic v2.
- (Optional) An existing web framework (such as Flask, Starlette, etc.) if you plan to integrate with one. If you don't have the framework installed, using the appropriate extra in pip (as shown below) will install it for you.

## Using pip

#### Install only FastOpenAPI
*The ordinary installation*
```bash
pip install fastopenapi
```

#### Install FastOpenAPI with a specific framework
*Useful if you're starting a new service and haven't installed a framework yet*
```bash
pip install fastopenapi[aiohttp]
```
```bash
pip install fastopenapi[falcon]
```
```bash
pip install fastopenapi[flask]
```
```bash
pip install fastopenapi[quart]
```
```bash
pip install fastopenapi[sanic]
```
```bash
pip install fastopenapi[starlette]
```
```bash
pip install fastopenapi[tornado]
```

---
