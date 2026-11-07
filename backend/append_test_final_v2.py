with open('tests/test_received_invoices.py', 'r', encoding='utf-8') as f:
    content = f.read()

with open('test_xxe_fragment.py', 'r', encoding='utf-8') as f:
    fragment = f.read()

content = content.rstrip() + '\n\n' + fragment

with open('tests/test_received_invoices.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Test XXE added successfully')
