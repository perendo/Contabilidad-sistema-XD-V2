with open('app/auth.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Encontrar el inicio y fin de la función _authenticate
start = None
end = None
for i, line in enumerate(lines):
    if line.startswith('def _authenticate('):
        start = i
    if start is not None and line.startswith('    return user'):
        end = i + 1
        break

if start is None or end is None:
    print(f"No se encontró la función. start={start}, end={end}")
else:
    new_func = '''def _authenticate(db: Session, email: str, password: str) -> User:
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
    return user
'''

    lines[start:end] = [new_func]
    with open('app/auth.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print('Updated successfully')
