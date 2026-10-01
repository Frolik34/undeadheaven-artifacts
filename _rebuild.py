# -*- coding: utf-8 -*-
"""Пересборка артефактов: у КАЖДОГО класснейма свои статы (balance.json -> global.json + база для калькулятора).

Как пользоваться:
  1. Правишь цифры в balance.json (значения конфига, целые числа).
  2. Запускаешь: python _rebuild.py
  3. Получаешь обновлённые global.json (с честными описаниями) и арты_база.js для калькулятора.

Единицы (тики каждые 3 сек; в описаниях и калькуляторе очки игрока = значение конфига x множитель):
  HP           addHP        x1    |  Прыжок   jumpBust    = 45 x очки
  Кровь        addBlood     x4    |  Скорость moveBoost   = 10 x очки
  Стойкость    addShock     x8    |  Защита от пуль     damageReduction.FIRE_ARM      x1
  Еда          ENERGY       x5    |  Защита от ударов   damageReduction.CLOSE_COMBAT  x1
  Вода         WATER        x5    |  Защита от аномалий damageReduction.STUN+EXPLOSION x1
  Выносливость STAMINA      x4    |
  Радиация     TOXICITY     x7    (+накопление / -вывод)
Флаги: brok = шанс перелома, bleed = вызывает кровотечение, hbl/hbr = лечение кровотечения/перелома,
       fall = сопротивление падению, punch = отбрасывание зомби (punchImpulse 70).
"""
import json, sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DIR = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(DIR, 'global_old.json')      # источник структуры (или global.json, если бэкапа нет)
if not os.path.exists(SRC):
    SRC = os.path.join(DIR, 'global.json')
OUT = os.path.join(DIR, 'global.json')
BAL = os.path.join(DIR, 'balance.json')
DB = os.path.join(DIR, 'арты_база.js')

# ---------- База по уникальным названиям (значения конфига, целые) ----------
BASE = {
    'Альфа-артефакт':        dict(bl=-12, sh=2,  en=4,  wa=-3, st=4,   tox=-5, brok=25),
    'Мёртвый Альфа-артефакт':dict(hp=11,  bl=-12, sh=-2, st=-3,  tox=-6, mb=2),
    'Ломоть мяса':           dict(hp=9,   bl=16,  en=9,  wa=-5,  st=-6,  tox=5, cc=-7),
    'Чёртов гриб':           dict(en=-1,  st=2,   tox=2, mb=2),
    'Сердце Чернобыля':      dict(bl=22,  sh=4,   en=-4, wa=-3,  st=-8,  tox=4),
    'Гиперкуб':              dict(sh=3,   en=-5,  wa=-4, st=7,   tox=5,  jb=5),
    'Капли':                 dict(sh=-1,  wa=4,   st=1,  tox=2,  hbr=1),
    'Плазма':                dict(sh=4,   st=11,  wa=-5, tox=7,  mb=10,  fa=5,  an=-12, fall=1),
    'Странный болт':         dict(bl=-15, sh=4,   wa=8,  tox=5,  jb=6,   an=-5, brok=25, fall=1),
    'Фонарь':                dict(hp=-6,  bl=8,   sh=-1, en=-3,  tox=-3, hbr=1),
    'Корона':                dict(bl=-9,  sh=1,   en=-1, wa=1,   tox=-4, mb=-1),
    'Колючка':               dict(hp=-6,  en=-4,  tox=6, mb=-6,  cc=10,  fa=12, an=15, punch=1),
    'Вспышка':               dict(bl=-6,  sh=2,   wa=-4, jb=5,   an=-4,  hbr=1),
    'Компас':                dict(hp=6,   en=-3,  wa=-3, st=5,   tox=2,  jb=5,  bleed=1),
    'Рог':                   dict(hp=8,   bl=-18, wa=5,  st=13,  tox=5,  mb=-6, fa=-5),
    'Кровь камня':           dict(hp=7,   bl=13,  sh=-2, st=-5,  tox=2,  hbl=1),
    'Кристалл':              dict(bl=-8,  sh=2,   wa=-3, tox=4,  fa=6,   cc=6,  hbr=1, punch=1),
    'Странный цветок':       dict(sh=-2,  en=-5,  tox=-6, jb=6,  fa=-4,  hbl=1, fall=1),
    'Сердце Оазиса':         dict(bl=11,  en=-5,  wa=5,  st=-6,  tox=-5, hbl=1, brok=25),
    'Батарейка':             dict(bl=6,   en=-4,  wa=6,  st=5,   tox=4,  mb=-1),
    'Брак':                  dict(bl=3,   en=1,   st=-1, hbl=1),
    'Крысиный король':       dict(sh=3,   en=5,   wa=-5, st=5,   tox=4,  cc=-3),
    'Грозовая ягода':        dict(sh=3,   wa=-5,  st=-6, tox=-7, jb=5,   bleed=1),
    'Грави':                 dict(hp=9,   bl=-6,  sh=3,  en=-4,  tox=2),
    'Золотая рыбка':         dict(en=7,   wa=7,   tox=5, mb=-4,  brok=20),
    'Огненный шар':          dict(bl=-7,  sh=1,   en=1,  st=-4,  tox=-4, mb=3),
    'Слизняк':               dict(bl=5,   wa=-2,  st=3,  tox=1,  brok=5),
    'Слизь':                 dict(sh=2,   wa=7,   en=-5, tox=-5, cc=-10, an=-10, hbr=1),
    'Морская звезда':        dict(hp=10,  wa=7,   st=-4, tox=6,  fa=5,   an=-5),
    'Сапфир':                dict(hp=-10, bl=13,  en=-6, wa=-3,  tox=-6, mb=3),
    'Арфа':                  dict(hp=-10, sh=4,   en=-5, wa=7,   tox=5,  cc=6,  punch=1),
    'Бифштекс':              dict(bl=8,   sh=-1,  en=7,  wa=-6,  tox=3,  hbl=1),
    'Битый камень':          dict(bl=-4,  en=-1,  wa=3,  tox=1,  jb=1),
    'Полость':               dict(bl=-3,  sh=1,   en=2,  st=-1,  tox=-1),
    'Вертушка':              dict(hp=2,   tox=1,  brok=5),
    'Факел':                 dict(bl=6,   sh=-1,  en=1,  wa=-1,  tox=-2),
    'Мухоловка':             dict(bl=9,   sh=2,   st=-3, tox=3,  mb=3,   bleed=1),
    'Галька':                dict(sh=-2,  en=-3,  wa=5,  st=4,   tox=4,  jb=5),
    'Гребень':               dict(bl=-6,  en=2,   wa=2,  tox=1,  mb=-1),
    'Попрыгунчик':           dict(hp=2,   en=-2,  wa=-1, tox=-1, hbr=1),
    'Лира':                  dict(hp=-2,  bl=3,   en=-1, wa=2),
    'Магма':                 dict(bl=-12, sh=2,   en=-5, tox=-7, mb=-3,  cc=6, fa=3, punch=1),
    'Мертвая губка':         dict(hp=-6,  en=-3,  tox=3, fa=5,   cc=5,   hbl=1, hbr=1),
    'Мясная зажигалка':      dict(bl=30,  en=-4,  wa=-8, st=-10, tox=-8, cc=5, fa=-8),
    'Плесень':               dict(bl=-11, sh=3,   en=-6, wa=-6,  tox=-7, jb=6, bleed=1, fall=1),
    'Кубик-рубик':           dict(sh=-2,  st=5,   wa=-4, tox=5,  jb=7,   cc=6, fa=6, fall=1),
    'Скорлупа':              dict(en=-4,  st=-5,  tox=5, mb=10,  cc=10,  fa=8, hbl=1, fall=1),
    'Шоколадка':             dict(bl=7,   sh=-1,  en=4,  wa=-1,  tox=1),
    'Слюда':                 dict(hp=-2,  sh=1,   wa=1,  st=-2,  tox=-2),
    'Сопля':                 dict(hp=10,  st=-4,  tox=3, jb=7,   mb=-4,  hbl=1, fall=1),
    'Странный котелок':      dict(hp=8,   bl=25,  wa=-8, tox=7,  cc=-5,  fa=-5, an=5),
    'Урок труда':            dict(bl=-25, st=8,   tox=-7, mb=12, fa=-6,  brok=20, fall=1),
    'Выверт':                dict(en=-6,  tox=-6, cc=-5, fa=4,   an=-4,  hbr=1),
    'Странная гайка':        dict(bl=22,  sh=3,   en=-6, st=-6,  tox=-5, cc=-5, bleed=1),
    'Завтрак туриста':       dict(hp=7,   en=8,   wa=8,  st=-9,  tox=7,  mb=10, bleed=1, fall=1),
    'Жидкий камень':         dict(sh=-2,  tox=4,  mb=4,  an=15,  hbl=1,  brok=20, punch=1),
}
SPECIAL = {'Странный котелок': '★ При смерти возвращает всё снаряжение на следующем респавне (артефакт сгорает)'}

DISP = {'hp': 1, 'bl': 4, 'sh': 8, 'en': 5, 'wa': 5, 'st': 4, 'tox': 7}
STAT_ORDER = ['hp', 'bl', 'sh', 'en', 'wa', 'st', 'tox']
STAT_NAMES = {'hp': 'Регенерация HP', 'bl': 'Кровь', 'sh': 'Стойкость', 'en': 'Еда',
              'wa': 'Вода', 'st': 'Выносливость', 'tox': 'Радиация'}
BONUS_ORDER = ['hp', 'bl', 'sh', 'en', 'wa', 'st', 'jb', 'mb', 'fa', 'cc', 'an']

def g(d, k):
    return d.get(k, 0)

def points(d):
    p = {k: g(d, k) * DISP[k] for k in STAT_ORDER}
    for k in ('jb', 'mb', 'fa', 'cc', 'an'):
        p[k] = g(d, k)
    return p

def apply_variant(stats, d, rank=0):
    """Вариация версии арта: +/-1 к главной (rank=0) или второй (rank=1) бонусной стате."""
    s = dict(stats)
    if d == 0:
        return s
    p = points(s)
    positives = sorted([k for k in BONUS_ORDER if p[k] > 0], key=lambda k: p[k], reverse=True)
    if not positives:
        return s
    k = positives[min(rank, len(positives) - 1)]
    s[k] = g(s, k) + d
    return s

def build_desc(name, d):
    p = points(d)
    parts = []
    def add(label, val, good_when_positive=True, suffix='/тик'):
        if val == 0:
            return
        good = (val > 0) == good_when_positive
        mark = '[+]' if good else '[-]'
        parts.append(f'{mark} {label}: {"+" if val > 0 else ""}{val}{suffix}')
    add(STAT_NAMES['hp'], p['hp'])
    add(STAT_NAMES['bl'], p['bl'])
    add(STAT_NAMES['sh'], p['sh'])
    add(STAT_NAMES['en'], p['en'])
    add(STAT_NAMES['wa'], p['wa'])
    add(STAT_NAMES['st'], p['st'], suffix='')
    add('Радиация (накопление)' if p['tox'] > 0 else 'Радиация (вывод)', p['tox'], good_when_positive=False)
    add('Прыжок', p['jb'], suffix='')
    add('Скорость', p['mb'], suffix='')
    add('Защита от пуль', p['fa'], suffix='')
    add('Защита от ударов', p['cc'], suffix='')
    add('Защита от аномалий', p['an'], suffix='')
    if g(d, 'hbl'):
        parts.append('[+] Лечение кровотечения')
    if g(d, 'hbr'):
        parts.append('[+] Лечение перелома')
    if g(d, 'bleed'):
        parts.append('[-] Кровотечение: шанс/тик')
    if g(d, 'brok'):
        parts.append(f'[-] Перелом ноги: {d["brok"]} шанс/тик')
    if name in SPECIAL:
        parts.append('[' + SPECIAL[name] + ']')
    return f'{name} | ' + ' '.join(parts)

W = {'hp': 1.0, 'bl': 0.3, 'sh': 0.6, 'en': 0.5, 'wa': 0.5, 'st': 0.6, 'tox': 0.45,
     'jb': 1.2, 'mb': 1.2, 'fa': 1.2, 'cc': 1.2, 'an': 1.0}

def budget(d):
    p = points(d)
    s = 0.0
    for k, w in W.items():
        v = p[k]
        s += (-v if k == 'tox' else v) * w
    s += 4 if g(d, 'hbl') else 0
    s += 4 if g(d, 'hbr') else 0
    s -= 4 if g(d, 'bleed') else 0
    s -= g(d, 'brok') * 0.25
    return s

def make_balance(classes_by_name):
    """Первая генерация: база + вариации по класснеймам внутри группы (каждый класснейм уникален)."""
    variants = {2: [(1, 0), (-1, 0)],
                3: [(1, 0), (0, 0), (-1, 0)],
                4: [(1, 0), (-1, 0), (1, 1), (-1, 1)]}
    arts = {}
    for name, clss in classes_by_name.items():
        vs = variants.get(len(clss), [(0, 0)] * len(clss))
        for cls, (d, rank) in zip(sorted(clss), vs):
            arts[cls] = apply_variant(BASE[name], d, rank)
    return arts

def main():
    with open(SRC, encoding='utf-8') as f:
        data = json.load(f)
    effs = data['effects']

    classes_by_name = {}
    for key, e in effs.items():
        title = e.get('Description', '').split('|')[0].strip()
        classes_by_name.setdefault(title, []).append(key)

    unknown = set(classes_by_name) - set(BASE)
    if unknown:
        print('!!! Нет в базе:', unknown)
        return

    if os.path.exists(BAL):
        with open(BAL, encoding='utf-8') as f:
            bal = json.load(f)
        arts = bal.get('арты', {})
        added = []
        for name, clss in classes_by_name.items():
            for cls in clss:
                if cls not in arts:
                    arts[cls] = dict(BASE[name])
                    added.append(cls)
        if added:
            print('Добавлены новые класснеймы в balance.json:', added)
            bal['арты'] = arts
            with open(BAL, 'w', encoding='utf-8') as f:
                json.dump(bal, f, ensure_ascii=False, indent=2)
    else:
        arts = make_balance(classes_by_name)
        bal = {'_справка': (
            'Правь цифры у нужного класснейма и запускай: python _rebuild.py — '
            'пересоберутся global.json и калькулятор. Значения конфига, целые числа. '
            'Очки игрока в описаниях: HP x1, Кровь x4, Стойкость x8, Еда x5, Вода x5, '
            'Выносливость x4, Радиация x7 (+накопление/-вывод), Прыжок x45 (45 за очко), '
            'Скорость x10 (10 за очко), защиты x1. Флаги: brok=шанс перелома, bleed=1 '
            'вызывает кровотечение, hbl/hbr=1 лечение кровотечения/перелома, fall=1 '
            'сопротивление падению, punch=1 отбрасывание зомби.'),
            'арты': arts}
        with open(BAL, 'w', encoding='utf-8') as f:
            json.dump(bal, f, ensure_ascii=False, indent=2)
        print('Создан balance.json (правь его для тонкой настройки)')

    report = []
    for key, e in effs.items():
        d = arts[key]
        title = e.get('Description', '').split('|')[0].strip()
        e['Description'] = build_desc(title, d)
        e['addHP'] = g(d, 'hp')
        e['addBlood'] = g(d, 'bl')
        e['addShock'] = g(d, 'sh')
        e['addBleedigSource'] = 1.0 if g(d, 'bleed') else 0.0
        e['brokingLegs'] = 1 if g(d, 'brok') else 0
        if g(d, 'brok'):
            e['BrokenLegsChance'] = d['brok']
        e['jumpBust'] = 45.0 * g(d, 'jb')
        e['moveBoost'] = 10.0 * g(d, 'mb')
        e['fallDamageResist'] = 1 if g(d, 'fall') else 0
        e['RemoveBleeding'] = 1 if g(d, 'hbl') else 0
        e['RemoveBrokenLegs'] = 1 if g(d, 'hbr') else 0
        pv = 70.0 if g(d, 'punch') else 0.0
        e['punchImpulse'] = {'ZOMBIE_BASE': pv, 'ANIMAL_BASE': pv, 'PLAYER_BASE': pv}
        e['damageReduction'] = {'FIRE_ARM': float(g(d, 'fa')), 'STUN': float(g(d, 'an')),
                                'CLOSE_COMBAT': float(g(d, 'cc')), 'EXPLOSION': float(g(d, 'an'))}
        vals = {'ENERGY': g(d, 'en'), 'WATER': g(d, 'wa'), 'STAMINA': g(d, 'st'), 'TOXICITY': g(d, 'tox')}
        for st in e['playerStats']:
            nm = st['name']
            if nm in vals:
                v = vals[nm]
                st['value'] = float(v)
                st['isNegativeEffect'] = 1 if (v > 0 if nm == 'TOXICITY' else v < 0) else 0
        report.append((budget(d), title, key))

    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f'OK: global.json пересобран ({len(effs)} эффектов)')

    # База для калькулятора (очки игрока)
    db = {}
    for key in effs:
        d = arts[key]
        title = data['effects'][key]['Description'].split('|')[0].strip()
        p = points(d)
        db[key] = {'name': title,
                   'hp': p['hp'], 'bl': p['bl'], 'sh': p['sh'], 'en': p['en'], 'wa': p['wa'],
                   'st': p['st'], 'tox': p['tox'], 'jb': p['jb'], 'mb': p['mb'],
                   'fa': p['fa'], 'cc': p['cc'], 'an': p['an'],
                   'hbl': g(d, 'hbl'), 'hbr': g(d, 'hbr'), 'bleed': g(d, 'bleed'),
                   'brok': g(d, 'brok'), 'fall': g(d, 'fall'), 'punch': g(d, 'punch')}
    with open(DB, 'w', encoding='utf-8') as f:
        f.write('// Сгенерировано _rebuild.py из balance.json — не правь руками, правь balance.json\n')
        f.write('window.ART_DB = ' + json.dumps(db, ensure_ascii=False, indent=1) + ';\n')
    print(f'OK: арты_база.js ({len(db)} артефактов)')

    report.sort(reverse=True)
    print('\nБюджет силы (сверху сильные):')
    for s, t, k in report:
        print(f'  {s:7.1f}  {t}  [{k}]')

if __name__ == '__main__':
    main()
