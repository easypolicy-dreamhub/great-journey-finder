#!/usr/bin/env python3
"""
GE "The Great Journey" Finder - monthly data refresh.

Opens the Great Eastern panel locator page, finds the current download links for the
Great Journey lists (hospitals, A&E outpatient hospitals, clinics, 24-hour clinics,
vaccination-programme clinics, pharmacies, physiotherapy centres), downloads the PDFs,
reads them, and rewrites the JSON files under data/.

Run:  python3 scripts/update_data.py
Needs: pip install requests beautifulsoup4 pdfplumber
Built to run unattended in GitHub Actions once a month.
"""
import difflib
import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
import pdfplumber

# ---------------------------------------------------------------------------
# Approximate town coordinates (used only for the "sort by distance" feature)
# ---------------------------------------------------------------------------
TOWN_COORDS = {
    "Alor Setar": (6.1210, 100.3690), "Ampang": (3.1500, 101.7622),
    "Batu Pahat": (1.8549, 102.9326), "Bayan Lepas": (5.2966, 100.2668),
    "Bintulu": (3.1729, 113.0414), "Bukit Mertajam": (5.3644, 100.4670),
    "Butterworth": (5.3991, 100.3638), "Cheras": (3.1073, 101.7414),
    "George Town": (5.4141, 100.3288), "Georgetown": (5.4141, 100.3288),
    "Ipoh": (4.5975, 101.0901), "Iskandar Puteri": (1.4241, 103.6357),
    "Johor Bahru": (1.4927, 103.7414), "Kajang": (2.9931, 101.7874),
    "Kangar": (6.4414, 100.1986), "Klang": (3.0333, 101.4500),
    "Kluang": (2.0311, 103.3186), "Kota Bahru": (6.1254, 102.2381),
    "Kota Kinabalu": (5.9804, 116.0735), "Kuala Lumpur": (3.1390, 101.6869),
    "Kuala Selangor": (3.3410, 101.2530), "Kuala Terengganu": (5.3302, 103.1408),
    "Kuantan": (3.8077, 103.3260), "Kuching": (1.5535, 110.3593),
    "Malacca": (2.1896, 102.2501), "Masai": (1.4661, 103.8963),
    "Melaka": (2.1896, 102.2501), "Miri": (4.3993, 113.9914),
    "Muar": (2.0442, 102.5689), "Nilai": (2.8145, 101.7965),
    "Nusajaya": (1.4241, 103.6357), "Pasir Gudang": (1.4726, 103.8998),
    "Penang": (5.4141, 100.3288), "Perai": (5.3833, 100.3833),
    "Petaling Jaya": (3.1073, 101.6067), "Puchong": (3.0219, 101.6172),
    "Rawang": (3.3186, 101.5772), "Segamat": (2.5142, 102.8159),
    "Senawang": (2.6667, 101.9500), "Seremban": (2.7297, 101.9381),
    "Seri Manjung": (4.2019, 100.6900), "Shah Alam": (3.0733, 101.5185),
    "Sibu": (2.2870, 111.8305), "Simpang Ampat": (5.2833, 100.4667),
    "Sitiawan": (4.2153, 100.6980), "Sri Gading": (1.9333, 102.9333),
    "Subang Jaya": (3.0567, 101.5851), "Sungai Petani": (5.6474, 100.4876),
    "Taiping": (4.8500, 100.7333), "Tanjung Bungah": (5.4667, 100.3000),
    "Teluk Intan": (4.0225, 101.0202), "Alor Gajah": (2.3785, 102.2088),
    "Ayer Itam": (5.4064, 100.2775), "Ayer Tawar": (4.1180, 100.7480),
    "Bahau": (2.8083, 102.4167), "Bangi": (2.9280, 101.7900),
    "Batu Berendam": (2.2515, 102.2650), "Batu Caves": (3.2379, 101.6840),
    "Batu Ferringhi": (5.4728, 100.2470), "Batu Gajah": (4.4650, 101.0390),
    "Batu Kawan": (5.2939, 100.4258), "Beranang": (2.8747, 101.8397),
    "Bidor": (4.1050, 101.2650), "Bukit Beruang": (2.2460, 102.2960),
    "Cameron Highlands": (4.4715, 101.3798), "Cyberjaya": (2.9213, 101.6559),
    "Dengkil": (2.8272, 101.6675), "Dungun": (4.7620, 103.4230),
    "Gelang Patah": (1.4270, 103.5960), "Gelugor": (5.3610, 100.3070),
    "Gemencheh": (2.5760, 102.2450), "Gopeng": (4.4560, 101.1830),
    "Gurun": (5.8140, 100.4610), "Hutan Melintang": (4.0430, 100.9950),
    "Jelebu": (2.9370, 101.8830), "Jelutong": (5.3970, 100.3080),
    "Jempol": (2.8600, 102.3670), "Jengka": (3.6110, 102.4130),
    "Jenjarom": (2.8080, 101.4270), "Jerantut": (3.9370, 102.3620),
    "Kahang": (2.1550, 103.2010), "Kampar": (4.3080, 101.1450),
    "Kamunting": (4.8570, 100.7290), "Kapar": (3.0940, 101.4180),
    "Karak": (3.4880, 101.9470), "Kemaman": (4.2350, 103.4170),
    "Keningau": (5.3380, 116.1610), "Kepala Batas": (5.5170, 100.4390),
    "Kota Tinggi": (1.7370, 103.9010), "Kuala Kangsar": (4.7710, 100.9370),
    "Kuala Krai": (5.5330, 102.2020), "Kuala Lipis": (4.1840, 102.0470),
    "Kuala Pilah": (2.7370, 102.2500), "Kulai": (1.6630, 103.6020),
    "Kulim": (5.3660, 100.5610), "Labis": (2.3870, 103.0210),
    "Lahad Datu": (5.0300, 118.3270), "Langkap": (4.2650, 100.9770),
    "Langkawi": (6.3500, 99.8000), "Limbang": (4.7500, 115.0080),
    "Lunas": (5.5860, 100.5330), "Mantin": (2.7290, 101.9260),
    "Marang": (5.2060, 103.2070), "Masjid Tanah": (2.3480, 102.0870),
    "Mentakab": (3.4830, 102.3540), "Mersing": (2.4310, 103.8400),
    "Nibong Tebal": (5.1670, 100.4830), "Pagoh": (2.1370, 102.7420),
    "Pantai Remis": (4.3960, 100.6560), "Papar": (5.7350, 115.9310),
    "Parit Buntar": (5.1210, 100.4900), "Pasir Mas": (6.0470, 102.1420),
    "Pekan": (3.4920, 103.3980), "Pekan Nanas": (1.5140, 103.4870),
    "Penampang": (5.9350, 116.1080), "Pokok Sena": (5.9420, 100.5100),
    "Pontian": (1.4870, 103.3900), "Port Dickson": (2.5220, 101.7960),
    "Ranau": (5.9540, 116.6580), "Rantau": (2.5940, 101.9820),
    "Raub": (3.7930, 101.8580), "Sandakan": (5.8402, 118.1179),
    "Sarikei": (2.1250, 111.5170), "Semenyih": (2.9450, 101.8420),
    "Semporna": (4.4820, 118.6110), "Senai": (1.5850, 103.6300),
    "Sepang": (2.7160, 101.7040), "Seri Kembangan": (3.0250, 101.7050),
    "Serian": (1.1670, 110.5830), "Skudai": (1.5340, 103.6570),
    "Sungai Bakap": (5.2280, 100.4870), "Sungai Besar": (3.6720, 100.9990),
    "Sungai Buloh": (3.2020, 101.5800), "Sungai Jawi": (5.2200, 100.4870),
    "Sungai Nibong": (5.3400, 100.3060), "Sungai Siput": (4.8250, 101.0870),
    "Tampin": (2.4680, 102.2300), "Tanah Merah": (5.8000, 102.1420),
    "Tangkak": (2.2680, 102.5510), "Tanjong Malim": (3.6880, 101.5170),
    "Tanjung Sepat": (2.6570, 101.5730), "Tanjung Tokong": (5.4460, 100.3070),
    "Tawau": (4.2440, 117.8910), "Telok Panglima Garang": (2.8500, 101.5330),
    "Temerloh": (3.4510, 102.4200), "Triang": (3.1590, 102.4720),
    "Tuaran": (6.1830, 116.2330), "Ulu Tiram": (1.5860, 103.8110),
    "W P Labuan": (5.2831, 115.2308), "Yong Peng": (2.0060, 103.0680),
    "Pulau Pinang": (5.4141, 100.3288),
}

EXTRA = {
 # Johor
 "Bukit Gambir": (2.27,102.66), "Simpang Renggam": (1.8167,103.2833), "Parit Raja": (1.8667,103.1167),
 "Bandar Penawar": (1.5333,104.2667), "Pengerang": (1.3833,104.1167), "Ibrahim International Business District": (1.4650,103.7600),
 "Muar Darul Takzim": (2.0442,102.5689), "Kulaijaya": (1.6630,103.6020), "Semerah": (1.8667,103.0833), "Endau": (2.6500,103.6167),
 "Benut": (1.7667,103.1000), "Tampoi": (1.5200,103.7000), "Plentong": (1.5200,103.8200),
 # Kedah
 "Jitra": (6.2667,100.4167), "Padang Serai": (5.4167,100.5667), "Pendang": (5.9964,100.4767), "Changlun": (6.4333,100.4333),
 "Kodiang": (6.3667,100.3000), "Bedong": (5.6833,100.5333), "Baling": (5.6764,100.9164), "Guar Chempedak": (5.8167,100.4333),
 "Kuala Ketil": (5.7833,100.6667), "Sik": (5.8167,100.7333), "Kuala Muda": (5.6500,100.4000), "Kuala Nerang": (6.2500,100.6167),
 "Sungai Lalang": (5.6500,100.6000),
 # Kelantan
 "Kota Bharu": (6.1254,102.2381), "Bachok": (6.0667,102.4000), "Pasir Puteh": (5.8333,102.4000), "Wakaf Bharu": (6.1500,102.2667),
 "Tumpat": (6.2000,102.1667), "Gua Musang": (4.8833,101.9667), "Machang": (5.7667,102.2167), "Jeli": (5.7000,101.8333),
 "Bandar Jeli": (5.7000,101.8333), "Ketereh": (5.9500,102.3000), "Kubang Kerian": (6.1167,102.2833),
 # Kuala Lumpur / Putrajaya / Labuan
 "Kuchai Lama": (3.0900,101.6900), "Bukit Jalil": (3.0600,101.6900), "Sungai Besi": (3.0700,101.7100), "Setapak": (3.1900,101.7100),
 "Putrajaya": (2.9264,101.6964),
 # Negeri Sembilan
 "Labu": (2.7833,101.8500), "Gemas": (2.5833,102.6167), "Bandar Enstek": (2.7000,101.7500), "Bandar Baru Enstek": (2.7000,101.7500),
 "Rembau": (2.5833,102.0900), "Sungai Gadut": (2.6500,102.0500), "Paroi": (2.7500,101.9500), "Kuala Klawang": (3.0667,102.0667),
 "Bandar Sri Sendayan": (2.6500,101.8000), "Sendayan": (2.6500,101.8000), "Sikamat": (2.6867,101.9633), "Ampangan": (2.6900,101.9550),
 "Rasah Jaya": (2.7333,101.9500),
 # Pahang
 "Bentong": (3.5226,101.9087), "Muadzam Shah": (3.0500,103.0333), "Bandar Bera": (3.3000,102.5000), "Bera": (3.3000,102.5000),
 "Tanah Rata": (4.4667,101.3833), "Kuala Rompin": (2.8000,103.4833), "Kuala Krau": (3.5833,102.3500), "Genting Highlands": (3.4236,101.7930),
 "Maran": (3.5833,102.7667),
 # Perak
 "Tapah": (4.1993,101.2630), "Chemor": (4.7167,101.1167), "Slim River": (3.8333,101.4000), "Tanjung Malim": (3.6833,101.5167),
 "Bagan Serai": (5.0100,100.5333), "Seri Iskandar": (4.3667,100.9667), "Bandar Seri Iskandar": (4.3667,100.9667), "Selama": (5.2167,100.6833),
 "Lumut": (4.2333,100.6333), "Tanjung Rambutan": (4.6700,101.1500), "Lenggong": (5.1000,100.9833), "Batu Kurau": (4.9700,100.8000),
 "Gerik": (5.4333,101.1333), "Sungkai": (3.9944,101.3028), "Semanggol": (5.0333,100.6167), "Lahat": (4.4667,101.0833),
 "Menglembu": (4.5500,101.0500), "Jelapang": (4.6333,101.0833), "Simpang Pulai": (4.5500,101.1500),
 # Perlis
 "Arau": (6.4297,100.2733), "Padang Besar": (6.6667,100.3167), "Beseri": (6.4600,100.1700), "Mukim Beseri": (6.4600,100.1700),
 # Sabah
 "Kota Marudu": (6.4833,116.7167), "Putatan": (5.8833,116.0500), "Beaufort": (5.3471,115.7451), "Menggatal": (6.0167,116.1000),
 "Pitas": (6.7000,117.0500), "Tamparuli": (6.1600,116.2700), "Kota Belud": (6.3500,116.4333), "Kudat": (6.8833,116.8333),
 "Tenom": (5.1333,115.9333), "Kunak": (4.6833,118.2500), "Sipitang": (5.0833,115.5500), "Inanam": (6.0333,116.1167),
 "Kota Kinaba": (5.9804,116.0735),
 # Sarawak
 "Kota Samarahan": (1.4600,110.4833), "Samarahan": (1.4600,110.4833), "Sri Aman": (1.2333,111.4667), "Bintangor": (2.1667,111.6167),
 "Betong": (1.4167,111.5167), "Mukah": (2.9000,112.0833), "Saratok": (1.7333,111.3667), "Bau": (1.4000,110.1500),
 "Kapit": (2.0167,112.9333), "Kanowit": (2.1167,112.1500), "Lundu": (1.6667,109.8667), "Lawas": (4.8500,115.4000),
 # Selangor
 "Puncak Alam": (3.2214,101.4375), "Bandar Puncak Alam": (3.2214,101.4375), "Banting": (2.8167,101.5000), "Hulu Langat": (3.1000,101.8500),
 "Batang Kali": (3.4333,101.6500), "Tanjong Karang": (3.4333,101.1667), "Bestari Jaya": (3.3833,101.4333), "Ijok": (3.3833,101.4333),
 "Tanjong Sepat": (2.6500,101.5833), "Teluk Panglima Garang": (2.8500,101.5333), "Sri Kembangan": (3.0250,101.7050), "Gombak": (3.2500,101.7167),
 "Jenjarum": (2.8080,101.4270), "Kuala Kubu Bharu": (3.5667,101.6500), "Kuala Kubu Baharu": (3.5667,101.6500), "Selayang": (3.2500,101.6500),
 "Selayang Jaya": (3.2500,101.6500), "Sg Buloh": (3.2020,101.5800), "Serendah": (3.3667,101.6000), "Subang Bestari": (3.0833,101.5333),
 "Bandar Bukit Raja": (3.0900,101.4700), "Jeram": (3.2000,101.3500), "Taman Megah": (3.1073,101.6067), "Bandar Sunway": (3.0670,101.6070),
 "Salak Tinggi": (2.8167,101.7000), "Bandar Baru Salak Tinggi": (2.8167,101.7000), "Damansara Perdana": (3.1700,101.6000),
 "Bukit Beruntung": (3.4500,101.5500), "Bandar Bukit Beruntung": (3.4500,101.5500), "Upm Serdang": (3.0000,101.7200),
 "Batu Cave": (3.2379,101.6840), "Sekinchan": (3.5167,101.1167), "Pj": (3.1073,101.6067),
 # Terengganu
 "Paka": (4.6333,103.4333), "Jerteh": (5.7333,102.4833), "Besut": (5.7833,102.5667), "Chukai": (4.2333,103.4167), "Cukai": (4.2333,103.4167),
 "Kerteh": (4.5167,103.4500), "Kuala Besut": (5.8333,102.5667), "Kemasik": (4.4167,103.4500), "Kuala Berang": (5.0667,103.0167),
 "Kuala Nerus": (5.3667,103.0833), "Kuala Terengganuterengganu": (5.3302,103.1408), "Pusat Bandar Jerteh": (5.7333,102.4833),
 # KL typos / aliases
 "Kl": (3.1390,101.6869), "K.L": (3.1390,101.6869), "Kuala Lmpur": (3.1390,101.6869), "Ttdi": (3.1360,101.6300),
}
CENTROIDS = {'Johor':(1.85,103.3),'Kedah':(6.1,100.6),'Kelantan':(5.5,102.1),'Melaka':(2.2,102.25),'Negeri Sembilan':(2.75,102.0),
 'Pahang':(3.8,102.6),'Penang':(5.4,100.3),'Perak':(4.6,101.1),'Perlis':(6.45,100.2),'Sabah':(5.4,116.9),'Sarawak':(2.0,112.9),
 'Selangor':(3.3,101.5),'Terengganu':(5.0,103.0),'Kuala Lumpur':(3.14,101.69),'Putrajaya':(2.93,101.69),'Labuan':(5.28,115.24)}

# ---------------------------------------------------------------------------
# PDF table reading
# ---------------------------------------------------------------------------

STATE_MAP = {
 'kedah':'Kedah','perlis':'Perlis','penang':'Penang','pulau pinang':'Penang','perak':'Perak',
 'selangor':'Selangor','wilayah persekutuan':'Kuala Lumpur','wilayah persekutuan kuala lumpur':'Kuala Lumpur',
 'kuala lumpur':'Kuala Lumpur','putrajaya':'Putrajaya','wilayah persekutuan putrajaya':'Putrajaya',
 'negeri sembilan':'Negeri Sembilan','melaka':'Melaka','johor':'Johor','pahang':'Pahang',
 'terengganu':'Terengganu','kelantan':'Kelantan','sabah':'Sabah','sarawak':'Sarawak',
 'labuan':'Labuan','wilayah persekutuan labuan':'Labuan',
}
def canon_state(raw):
    return STATE_MAP.get(re.sub(r'\s+',' ',(raw or '').strip().lower()))

def clean(x):
    return re.sub(r'\s+',' ',(x or '').replace('\n',' ')).strip()

def read_rows(pdf_path, heading_states=False):
    """Yield dicts: state, brand, cells(raw list), for every numbered data row."""
    out=[]; state=None; brand=None
    with pdfplumber.open(pdf_path) as pdf:
        for p in pdf.pages:
            tabs=sorted(p.find_tables(), key=lambda t:t.bbox[1]); prev=0
            for t in tabs:
                top=t.bbox[1]
                if heading_states and top-prev>2:
                    txt=p.crop((0,max(prev,0),p.width,top)).extract_text() or ''
                    for line in txt.split('\n'):
                        s=canon_state(line)
                        if s: state=s
                for r in t.extract():
                    c0=clean(r[0])
                    rest=[x for x in r[1:] if x]
                    if re.fullmatch(r'\d+',c0):
                        out.append({'state':state,'brand':brand,'cells':[x or '' for x in r]})
                    elif c0 and not rest:
                        m=re.match(r'The Great Journey Pharmacy \((.+?)\)',c0)
                        if m: brand=m.group(1)
                        else:
                            s=canon_state(c0)
                            if s: state=s
                prev=t.bbox[3]
    return out

# ---------------------------------------------------------------------------
# Town / coordinate lookup
# ---------------------------------------------------------------------------

STATE_WORDS = ['kedah','perlis','penang','pulau pinang','perak','selangor','kuala lumpur','putrajaya','negeri sembilan',
 'melaka','malacca','johor','pahang','terengganu','kelantan','sabah','sarawak','labuan','wilayah persekutuan','malaysia',
 'darul aman','darul ehsan','darulaman','darul ta\'zim','federal territory','wp','wpkl','n.s.d.k','nsdk','kedah darul aman']

def extract_town(addr):
    a=clean(addr)
    # 1) town after a 5-digit postcode
    m=re.search(r'\b\d{5}\b[,\s]+([A-Za-z][A-Za-z .\'’/-]*?)(?=\s*(?:,|$|\d))',a)
    cands=[]
    if m: cands.append(m.group(1).strip(' .,'))
    # 2) segment just before the postcode
    m2=re.search(r'([A-Za-z][A-Za-z .\'’/-]*?)[,\s]+\b\d{5}\b',a)
    if m2: cands.append(m2.group(1).strip(' .,').split(',')[-1].strip())
    # 3) last non-state comma segment
    parts=[p.strip(' .') for p in a.split(',') if p.strip(' .')]
    for p in reversed(parts):
        pl=re.sub(r'\d{5}','',p).strip().lower()
        if pl and pl not in STATE_WORDS and not re.search(r'\d',pl): cands.append(re.sub(r'\d{5}','',p).strip()); break
    out=[]
    for c in cands:
        c=re.sub(r'\b(wilayah persekutuan|federal territory|kedah|perlis|penang|pulau pinang|perak|selangor|kuala lumpur|putrajaya|negeri sembilan|melaka|malacca|johor|pahang|terengganu|kelantan|sabah|sarawak|labuan|malaysia|darul ehsan|darul aman|darulaman|wpkl|wp)\b','',c,flags=re.I)
        c=re.sub(r'\s+',' ',c).strip(' .,-')
        if c and c.lower() not in STATE_WORDS and not re.search(r'\d',c): out.append(c)
    return out

def lookup_coord(addr, state, towns, centroids):
    for c in extract_town(addr):
        key=c.title()
        if key in towns: return towns[key], 'town'
        # try progressively: last word(s)
        words=key.split()
        for n in range(len(words),0,-1):
            k=' '.join(words[-n:])
            if k in towns: return towns[k],'town'
    # whole-address scan for any known town name (longest first)
    low=clean(addr).lower()
    for t in sorted(towns,key=len,reverse=True):
        if len(t)>=5 and re.search(r'\b'+re.escape(t.lower())+r'\b',low): return towns[t],'town'
    if state in centroids: return centroids[state],'state'
    return (None,None),'none'

# ---------------------------------------------------------------------------
# Locator page: find the 7 current Great Journey PDF links
# ---------------------------------------------------------------------------
LOCATOR_URL = "https://www.greateasternlife.com/my/en/customer-services/healthcare-services/healthcare-overview/locators-search-page.html"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
TMP_DIR = Path("/tmp/gj-pdfs")

DEFAULT_AE_DIAGNOSES = ["Dengue Fever", "Zika Virus", "Chikungunya Fever", "Acute Gastroenteritis", "Influenza A", "Influenza B",
                        "Hand, Foot and Mouth Disease", "Bronchitis", "Pneumonia", "Bronchiolitis", "Tonsillitis", "Sinusitis"]
REQUIRED = ["hospital", "clinic", "pharmacy", "physio"]          # run fails if any is missing
OPTIONAL = ["hospital_ae", "clinic24", "vaccination"]            # kept from last month if missing
MIN_COUNTS = {"hospital": 30, "clinic": 500, "pharmacy": 300, "physio": 40}


def classify(text):
    """Work out which of our 7 lists a download link is, from its button text."""
    t = " ".join(text.split()).lower()
    if "great journey" not in t:
        return None            # e.g. the non-Great-Journey Panel Hospital / Specialist / Clinic lists
    if "pharmacy" in t:
        return "pharmacy"
    if "physiotherapy" in t:
        return "physio"
    if "hospital" in t:
        return "hospital_ae" if ("accident" in t or "a&e" in t or "emergency" in t) else "hospital"
    if "clinic" in t:
        if "24 hours" in t or "24 hour" in t:
            return "clinic24"
        if "vaccination" in t:
            return "vaccination"
        return "clinic"
    return None


def find_pdf_links():
    resp = requests.get(LOCATOR_URL, headers=HEADERS, timeout=45)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    links = {}
    for a in soup.find_all("a", href=True):
        if not a["href"].lower().split("?")[0].endswith(".pdf"):
            continue
        key = classify(a.get_text(" ", strip=True))
        if key and key not in links:
            links[key] = urljoin(LOCATOR_URL, a["href"])
    missing = [k for k in REQUIRED if k not in links]
    if missing:
        raise RuntimeError(f"Could not find the download link(s) for: {missing}. The Great Eastern page layout may have changed.")
    for k in OPTIONAL:
        if k not in links:
            print(f"  note: no link found for optional list '{k}' - keeping last month's data for it")
    return links


def download(url, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    r = requests.get(url, headers=HEADERS, timeout=120)
    r.raise_for_status()
    if not r.content.startswith(b"%PDF"):
        raise RuntimeError(f"{url} did not return a PDF")
    dest.write_bytes(r.content)
    return dest


# ---------------------------------------------------------------------------
# Dates printed on the PDFs (fall back to the date in the file name)
# ---------------------------------------------------------------------------
MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


def pdf_text(path):
    with pdfplumber.open(path) as pdf:
        return "\n".join((p.extract_text() or "") for p in pdf.pages)


def find_date(text, url):
    m = re.search(r"Updated as (?:of|at)\s+(\d{1,2})/(\d{1,2})/(\d{4})", text)
    if m:
        d, mo, y = map(int, m.groups())
        return {"iso": f"{y:04d}-{mo:02d}-{d:02d}", "precision": "day", "source": "pdf"}
    m = re.search(r"Updated as (?:of|at)\s+(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", text)
    if m and m.group(2)[:3].lower() in MONTHS:
        d, y = int(m.group(1)), int(m.group(3))
        mo = MONTHS[m.group(2)[:3].lower()]
        return {"iso": f"{y:04d}-{mo:02d}-{d:02d}", "precision": "day", "source": "pdf"}
    name = url.rsplit("/", 1)[-1]
    m = re.search(r"(\d{1,2})([A-Za-z]{3,9})(\d{4})", name)
    if m and m.group(2)[:3].lower() in MONTHS:
        d, y = int(m.group(1)), int(m.group(3))
        return {"iso": f"{y:04d}-{MONTHS[m.group(2)[:3].lower()]:02d}-{d:02d}", "precision": "day", "source": "filename"}
    m = re.search(r"[-_]([A-Za-z]{3,9})[-_](\d{4})", name)
    if m and m.group(1)[:3].lower() in MONTHS:
        return {"iso": f"{int(m.group(2)):04d}-{MONTHS[m.group(1)[:3].lower()]:02d}-01", "precision": "month", "source": "filename"}
    return {"iso": None, "precision": None, "source": None}


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------
TOWNS = dict(TOWN_COORDS)
TOWNS.update(EXTRA)


def place(rec, address, state):
    (lat, lng), kind = lookup_coord(address, state, TOWNS, CENTROIDS)
    rec["lat"], rec["lng"], rec["geo"] = lat, lng, kind
    return rec


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def split_name(raw):
    lines = [clean(x) for x in (raw or "").split("\n") if clean(x)]
    return (lines[0] if lines else ""), (" ".join(lines[1:]) if len(lines) > 1 else "")


def build_hospitals(path):
    out = []
    for r in read_rows(path):
        c = r["cells"] + [""] * 6
        name, aka = split_name(c[1])
        # names that wrap onto a 2nd line without a "formerly known as" note
        if aka and not re.search(r"formerly|formely", aka, re.I):
            name, aka = clean(c[1]), ""
        aka = aka.strip("() ")
        rec = {"no": int(clean(c[0])), "name": name, "aka": aka, "address": clean(c[2]), "tel": clean(c[3]),
               "deposit": clean(c[4]), "ae": clean(c[5]).lower().startswith("y"), "state": r["state"]}
        out.append(place(rec, rec["address"], rec["state"]))
    return out


def build_ae(path):
    names, diagnoses = [], []
    for r in read_rows(path):
        c = r["cells"] + [""] * 4
        if len([x for x in r["cells"] if clean(x)]) >= 4:
            names.append(norm(split_name(c[1])[0]))
        elif clean(c[1]):
            diagnoses.append(clean(c[1]))
    return names, diagnoses


def build_clinics(main_path, h24_path, prev_h24):
    out = []
    for r in read_rows(main_path):
        c = r["cells"] + [""] * 4
        rec = {"no": int(clean(c[0])), "name": clean(c[1]), "address": clean(c[2]), "tel": clean(c[3]),
               "state": r["state"], "h24": False}
        out.append(place(rec, rec["address"], rec["state"]))
    by_name = {norm(x["name"]): x for x in out}
    by_tel = {re.sub(r"\D", "", x["tel"])[:9]: x for x in out if x["tel"]}
    if h24_path:
        for r in read_rows(h24_path):
            c = r["cells"] + [""] * 5
            hit = by_name.get(norm(c[1])) or by_tel.get(re.sub(r"\D", "", c[3])[:9])
            if hit:
                hit["h24"] = True
            else:   # listed as 24-hour but missing from the main list: keep it, flagged 24h
                rec = {"no": None, "name": clean(c[1]), "address": clean(c[2]), "tel": clean(c[3]),
                       "state": r["state"], "h24": True}
                out.append(place(rec, rec["address"], rec["state"]))
    else:
        for x in out:
            x["h24"] = norm(x["name"]) in prev_h24
    return out


def build_simple(path, kind):
    out = []
    for r in read_rows(path):
        c = r["cells"] + [""] * 4
        hours = "; ".join(clean(x).rstrip(";").strip() for x in (c[3] or "").split("\n") if clean(x).rstrip(";").strip())
        rec = {"no": int(clean(c[0])), "name": clean(c[1]), "address": clean(c[2]), "hours": hours, "state": r["state"]}
        if kind == "pharmacy":
            rec["brand"] = r["brand"]
        out.append(place(rec, rec["address"], rec["state"]))
    return out


def build_vaccination(path, clinics):
    by_name = {norm(x["name"]): x for x in clinics}
    keys = list(by_name)
    out = []
    for r in read_rows(path, heading_states=True):
        c = r["cells"] + [""] * 5
        rec = {"name": clean(c[1]), "address": clean(c[2]), "dengue": clean(c[3]), "influenza": clean(c[4]),
               "state": r["state"], "tel": ""}
        hit = by_name.get(norm(rec["name"]))
        if not hit:
            close = difflib.get_close_matches(norm(rec["name"]), keys, n=1, cutoff=0.93)
            cand = by_name[close[0]] if close else None
            hit = cand if cand and cand["state"] == rec["state"] else None
        if hit:
            rec["tel"] = hit["tel"]
        out.append(place(rec, rec["address"], rec["state"]))
    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def load_json(name, default):
    p = DATA_DIR / name
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(name, obj):
    p = DATA_DIR / name
    p.write_text(json.dumps(obj, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    print(f"  wrote {name} ({p.stat().st_size:,} bytes)")


def main():
    print("Finding current PDF links on the Great Eastern locator page...")
    links = find_pdf_links()
    for k, v in links.items():
        print(f"  {k}: {v}")

    prev_meta = load_json("meta.json", {})
    prev_clinics = load_json("clinics.json", [])
    prev_h24 = {norm(c["name"]) for c in prev_clinics if c.get("h24")}

    print("Downloading PDFs...")
    paths = {k: download(u, TMP_DIR / f"{k}.pdf") for k, u in links.items()}

    updated = dict(prev_meta.get("updated", {}))
    sources = dict(prev_meta.get("sources", {}))
    for k, p in paths.items():
        updated[k] = find_date(pdf_text(p), links[k])
        sources[k] = links[k]

    print("Parsing...")
    hospitals = build_hospitals(paths["hospital"])
    # The appendix of covered diagnoses is a picture inside the A&E PDF (no text to read), so we keep the
    # list below unless a text version ever appears. Review it if Great Eastern changes the appendix.
    ae_diag = prev_meta.get("ae_diagnoses") or DEFAULT_AE_DIAGNOSES
    if "hospital_ae" in paths:
        ae_names, diag = build_ae(paths["hospital_ae"])
        if diag:
            ae_diag = diag
        flagged = {norm(h["name"]) for h in hospitals if h["ae"]}
        if flagged != set(ae_names):
            print(f"  warning: A&E list ({len(ae_names)}) and the A&E column of the hospital list ({len(flagged)}) differ")
    clinics = build_clinics(paths["clinic"], paths.get("clinic24"), prev_h24)
    pharmacies = build_simple(paths["pharmacy"], "pharmacy")
    physio = build_simple(paths["physio"], "physio")
    if "vaccination" in paths:
        vaccination = build_vaccination(paths["vaccination"], clinics)
    else:
        vaccination = load_json("vaccination.json", [])

    counts = {"hospital": len(hospitals), "clinic": len(clinics), "pharmacy": len(pharmacies), "physio": len(physio)}
    print("  counts:", counts, "| vaccination:", len(vaccination))

    # Safety checks: never overwrite good data with a failed / partial read.
    for k, floor in MIN_COUNTS.items():
        if counts[k] < floor:
            raise RuntimeError(f"{k}: only {counts[k]} records found (expected at least {floor}). The PDF format may have changed. Refusing to overwrite.")
    for fname, key, n in [("hospitals.json", "hospital", counts["hospital"]), ("clinics.json", "clinic", counts["clinic"]),
                          ("pharmacies.json", "pharmacy", counts["pharmacy"]), ("physio.json", "physio", counts["physio"])]:
        old = len(load_json(fname, []))
        if old and n < old * 0.5:
            raise RuntimeError(f"{fname}: {n} records now vs {old} before - looks like a parsing failure. Refusing to overwrite.")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    states = sorted({x["state"] for ds in (hospitals, clinics, pharmacies, physio, vaccination) for x in ds if x.get("state")})
    brands = sorted({x["brand"] for x in pharmacies if x.get("brand")})
    write_json("hospitals.json", hospitals)
    write_json("clinics.json", clinics)
    write_json("pharmacies.json", pharmacies)
    write_json("physio.json", physio)
    write_json("vaccination.json", vaccination)
    write_json("meta.json", {"updated": updated, "sources": sources, "states": states, "brands": brands,
                             "ae_diagnoses": ae_diag, "counts": {**counts, "vaccination": len(vaccination)}})
    print("Done.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
