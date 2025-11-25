with open('cogs/setup.py', 'rb') as f:
    content = f.read().decode('utf-8', errors='ignore')
    
classes_to_find = ['ViewAdd', 'RolesDropdown', 'ChannelsDropdown', 'AddRemoveButtons']

for cls in classes_to_find:
    if f'class {cls}' in content:
        print(f'{cls}: DEFINED')
    else:
        print(f'{cls}: MISSING')

if 'ViewAdd' in content and 'class ViewAdd' not in content:
    print('\nViewAdd is referenced but NOT defined as a class')

lines = content.split('\n')
print(f'\nTotal lines: {len(lines)}')
