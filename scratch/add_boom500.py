path = 'dashboard/realtime_dashboard.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read().replace('\r\n', '\n')

target = 'MALAYSIAN_SNR_PRUNED_INFO = {\n'
boom_entry = '    "Boom 500 Index": "Poda confirmada en replay 2 años Malaysian SNR: Win Rate 28.0%, -$4,497.43 USD. Ruido de mechas y caídas continuas antes de retesteo.",\n'
if 'Boom 500 Index' not in text.split('MALAYSIAN_SNR_PRUNED_INFO = {')[1].split('}')[0]:
    text = text.replace(target, target + boom_entry)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    print('Boom 500 Index agregado a MALAYSIAN_SNR_PRUNED_INFO')
else:
    print('Ya estaba')
