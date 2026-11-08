import re

with open('app/auth.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Buscar y reemplazar la función _authenticate completa
old = '''def _authenticate(db: Session, email: str, password: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if user is None or not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )
    return user'''

new = '''def _authenticate(db: Session, email: str, password: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        # Usar hash falso para evitar ataques de tiempo (timing attack):
        # siempre ejecutar bcrypt.checkpw aunque el usuario no exista
        bcrypt.checkpw(password.encode(), bcrypt.hashpw(b"dummy", bcrypt.gensalt()).decode())
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )
    if not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )
    return user'''

if old in content:
    content = content.replace(old, new)
    with open('app/auth.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated successfully')
else:
    print("OLD STRING NOT FOUND")
    # Debug: mostrar lo que hay alrededor de _authenticate
    match = re.search(r'def _authenticate.*?return user', content, re.DOTALL)
    if match:
        print("Found:", repr(match.group()))
    else:
        print("Function not found at all")
