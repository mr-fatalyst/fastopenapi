# Instalación

FastOpenAPI está disponible en PyPI y es compatible con **Python 3.10 o superior**. Puedes instalar solo la biblioteca principal o incluir dependencias opcionales para frameworks web específicos.

## Requisitos previos

- **Python 3.10 o superior** – requerido debido al uso de tipado moderno y Pydantic v2.
- (Opcional) Un framework web existente (como Flask, Starlette, etc.), si planeas integrarlo. Si no lo tienes instalado, puedes usar los extras para instalarlo junto con FastOpenAPI.

## Instalación con pip

#### Solo instalar FastOpenAPI  
*Instalación básica:*
```bash
pip install fastopenapi
```

#### Instalar FastOpenAPI con un framework específico  
*Útil si comienzas un nuevo servicio sin haber instalado aún el framework:*
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
