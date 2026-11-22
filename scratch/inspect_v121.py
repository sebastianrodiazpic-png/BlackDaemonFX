with open('tests/test_v121_instruments_tri_motor_worker_control.py', 'r', encoding='utf-8') as f:
    text = f.read()

pos = text.find('assert "ESTRATEGIA ICT')
if pos == -1:
    pos = text.find('assert "ESTRATEGIA')
print(text[max(0, pos-200):min(len(text), pos+300)])
