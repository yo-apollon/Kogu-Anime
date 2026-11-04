import os
import json
import subprocess
import re
import html as htmllib
import time

HEADERS_CURL = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"

CARDS_DIR = "docs/assets/cards"
ERA_CACHE_DIR = ".cache/era_photos"
os.makedirs(CARDS_DIR, exist_ok=True)
os.makedirs(ERA_CACHE_DIR, exist_ok=True)

TARGETS = {
    # MMA
    "alex-pereira": (
        "Alex Pereira Glory Kickboxing fight",
        "Alex Pereira UFC 281 Adesanya middleweight champion knockout",
        "Alex Pereira UFC 300 Jamahal Hill champion bow arrow"
    ),
    "ronda-rousey": (
        "Ronda Rousey Strikeforce armbar debut",
        "Ronda Rousey UFC 157 first female champion belt",
        "Ronda Rousey UFC Hall of Fame legend"
    ),
    "alex-volkanovski": (
        "Alexander Volkanovski early rugby UFC debut",
        "Alexander Volkanovski UFC 245 Max Holloway champion",
        "Alexander Volkanovski UFC featherweight champion pound for pound belt"
    ),
    "fedor-emelianenko": (
        "Fedor Emelianenko Combat Sambo Russia tournament",
        "Fedor Emelianenko Pride FC Heavyweight Champion belt 2003",
        "Fedor Emelianenko The Last Emperor MMA legend"
    ),
    "sean-omalley": (
        "Sean O'Malley Dana White Contender Series knockout",
        "Sean O'Malley UFC 292 Sterling bantamweight champion belt",
        "Sean O'Malley Suga superstar UFC"
    ),
    "wanderlei-silva": (
        "Wanderlei Silva IVC Vale Tudo Brazil",
        "Wanderlei Silva Pride FC Middleweight Champion The Axe Murderer",
        "Wanderlei Silva UFC Pride MMA legend"
    ),
    "royce-gracie": (
        "Royce Gracie UFC 1 kimono Gi 1993",
        "Royce Gracie UFC 2 4 tournament champion",
        "Royce Gracie UFC Hall of Fame pioneer legend"
    ),
    "justin-gaethje": (
        "Justin Gaethje WSOF lightweight champion",
        "Justin Gaethje UFC 249 Tony Ferguson interim champion belt",
        "Justin Gaethje UFC BMF belt knockout"
    ),
    "dricus-du-plessis": (
        "Dricus Du Plessis KSW welterweight champion",
        "Dricus Du Plessis UFC 297 Sean Strickland middleweight belt",
        "Dricus Du Plessis Stillknocks UFC champion"
    ),
    "max-holloway": (
        "Max Holloway young UFC debut featherweight",
        "Max Holloway UFC 212 Jose Aldo champion belt",
        "Max Holloway UFC 300 Justin Gaethje BMF knockout champion"
    ),
    "paddy-pimblett": (
        "Paddy Pimblett Cage Warriors featherweight champion",
        "Paddy Pimblett UFC debut Luigi Vendramini knockout",
        "Paddy Pimblett The Baddy UFC London star"
    ),
    "stipe-miocic": (
        "Stipe Miocic Golden Gloves boxing wrestling debut",
        "Stipe Miocic UFC 198 Fabricio Werdum champion belt",
        "Stipe Miocic UFC heavyweight record title defenses legend"
    ),
    "nate-diaz": (
        "Nate Diaz The Ultimate Fighter 5 finale champion",
        "Nate Diaz UFC 196 Conor McGregor submission celebration",
        "Nate Diaz 209 Stockton BMF icon"
    ),
    "belal-muhammad": (
        "Belal Muhammad Titan FC welterweight champion",
        "Belal Muhammad UFC 10 fight win streak",
        "Belal Muhammad UFC 304 Leon Edwards champion belt"
    ),
    "georges-st-pierre": (
        "Georges St-Pierre early UFC welterweight debut 2004",
        "Georges St-Pierre UFC welterweight champion 9 title defenses",
        "Georges St-Pierre UFC 217 Michael Bisping middleweight champion belt"
    ),
    "francis-ngannou": (
        "Francis Ngannou Paris MMA 100% fight debut",
        "Francis Ngannou UFC 260 Stipe Miocic knockout champion belt",
        "Francis Ngannou PFL Super Fights Heavyweight Champion belt"
    ),
    "colby-covington": (
        "Colby Covington NCAA All-American Oregon State wrestling",
        "Colby Covington UFC 225 Rafael dos Anjos interim belt",
        "Colby Covington Chaos MAGA championship challenger"
    ),
    "conor-mcgregor": (
        "Conor McGregor Cage Warriors double champion 2012",
        "Conor McGregor UFC 194 Jose Aldo 13 seconds knockout belt",
        "Conor McGregor UFC 205 Eddie Alvarez Champ Champ two belts"
    ),
    "valentina-shevchenko": (
        "Valentina Shevchenko Muay Thai IFMA World Champion",
        "Valentina Shevchenko UFC Flyweight Champion belt 7 defenses",
        "Valentina Shevchenko Bullet UFC champion"
    ),
    "islam-makhachev": (
        "Islam Makhachev Combat Sambo World Champion",
        "Islam Makhachev UFC 280 Charles Oliveira champion belt",
        "Islam Makhachev UFC pound for pound number 1 champion"
    ),
    "demetrious-johnson": (
        "Demetrious Johnson WEC bantamweight debut",
        "Demetrious Johnson UFC Flyweight Champion 11 title defenses belt",
        "Demetrious Johnson ONE Championship World Title flying knee"
    ),
    "dustin-poirier": (
        "Dustin Poirier WEC early UFC featherweight",
        "Dustin Poirier UFC 236 Max Holloway interim lightweight belt",
        "Dustin Poirier UFC 257 Conor McGregor knockout The Diamond"
    ),
    "anderson-silva": (
        "Anderson Silva Shooto Pride FC Chute Boxe",
        "Anderson Silva UFC 77 Rich Franklin Vitor Belfort front kick belt",
        "Anderson Silva The Spider UFC Middleweight GOAT Hall of Fame"
    ),
    "tom-aspinall": (
        "Tom Aspinall Cage Warriors heavyweight debut",
        "Tom Aspinall UFC London heavyweight submission",
        "Tom Aspinall UFC 295 Sergei Pavlovich interim heavyweight champion belt"
    ),

    # Basketball
    "victor-wembanyama": (
        "Victor Wembanyama Metropolitans 92 France basketball",
        "Victor Wembanyama San Antonio Spurs NBA Rookie of the Year",
        "Victor Wembanyama The Alien 5x5 statline Spurs"
    ),
    "dwyane-wade": (
        "Dwyane Wade Marquette NCAA Final Four 2003",
        "Dwyane Wade 2006 NBA Finals MVP Miami Heat champion",
        "Dwyane Wade Miami Heat Big Three 3 rings Hall of Fame"
    ),
    "joel-embiid": (
        "Joel Embiid Kansas Jayhawks 2014 basketball",
        "Joel Embiid 2023 NBA MVP Philadelphia 76ers trophy",
        "Joel Embiid 70 points game The Process 76ers"
    ),
    "james-harden": (
        "James Harden Arizona State OKC Sixth Man of Year",
        "James Harden 2018 NBA MVP Houston Rockets",
        "James Harden 3-time scoring champion The Beard"
    ),
    "magic-johnson": (
        "Magic Johnson Michigan State NCAA 1979 champion",
        "Magic Johnson 1980 NBA Finals rookie MVP Lakers",
        "Magic Johnson Showtime Lakers 5 championships trophy"
    ),
    "wilt-chamberlain": (
        "Wilt Chamberlain Harlem Globetrotters Kansas basketball",
        "Wilt Chamberlain 100 point game Philadelphia Warriors",
        "Wilt Chamberlain 1972 Lakers NBA Champion Finals MVP"
    ),
    "bill-russell": (
        "Bill Russell San Francisco Dons NCAA back to back champion",
        "Bill Russell Boston Celtics 11 NBA championships rings",
        "Bill Russell NBA Finals MVP trophy namesake legend"
    ),
    "tim-duncan": (
        "Tim Duncan Wake Forest Demon Deacons 1997",
        "Tim Duncan 1999 NBA Finals MVP San Antonio Spurs first ring",
        "Tim Duncan 5 NBA championships The Big Fundamental Spurs"
    ),
    "damian-lillard": (
        "Damian Lillard Weber State 2012 basketball",
        "Damian Lillard Portland Trail Blazers Dame Time buzzer beater",
        "Damian Lillard NBA 75th Anniversary 71 points All-Star MVP"
    ),
    "kyrie-irving": (
        "Kyrie Irving Duke Blue Devils 2011",
        "Kyrie Irving 2016 NBA Finals Game 7 shot Cleveland Cavaliers",
        "Kyrie Irving Dallas Mavericks NBA Finals 2024 Uncle Drew"
    ),
    "jimmy-butler": (
        "Jimmy Butler Marquette Chicago Bulls Most Improved Player",
        "Jimmy Butler 2020 NBA Finals triple double Miami Heat",
        "Jimmy Butler Playoff Jimmy 56 points Miami Heat"
    ),
    "dirk-nowitzki": (
        "Dirk Nowitzki DJK Wurzburg Germany 1998",
        "Dirk Nowitzki 2007 NBA MVP Dallas Mavericks",
        "Dirk Nowitzki 2011 NBA Finals Champion MVP Dallas Mavericks trophy"
    ),
    "jayson-tatum": (
        "Jayson Tatum Duke Blue Devils 2017 basketball",
        "Jayson Tatum Eastern Conference Finals MVP 2022 Boston Celtics",
        "Jayson Tatum 2024 NBA Champion Boston Celtics trophy"
    ),
    "kevin-durant": (
        "Kevin Durant Texas Longhorns 2007 college player of year",
        "Kevin Durant 2014 NBA MVP Oklahoma City Thunder speech",
        "Kevin Durant Golden State Warriors back to back Finals MVP trophy"
    ),
    "anthony-edwards": (
        "Anthony Edwards Georgia Bulldogs 2020",
        "Anthony Edwards Minnesota Timberwolves playoff poster dunk",
        "Anthony Edwards USA Olympic Gold Medal Paris 2024 Ant-Man"
    ),
    "kawhi-leonard": (
        "Kawhi Leonard San Diego State 2011",
        "Kawhi Leonard 2014 NBA Finals MVP San Antonio Spurs",
        "Kawhi Leonard 2019 Toronto Raptors champion buzzer beater Finals MVP"
    ),
    "ja-morant": (
        "Ja Morant Murray State NCAA tournament 2019",
        "Ja Morant 2020 NBA Rookie of the Year Memphis Grizzlies",
        "Ja Morant All-NBA superstar poster dunk Grizzlies"
    ),
    "larry-bird": (
        "Larry Bird Indiana State 1979 NCAA final",
        "Larry Bird 1984 1986 NBA 3-time MVP Boston Celtics",
        "Larry Bird 3 NBA championships Hall of Fame Larry Legend"
    ),

    # Football
    "karim-benzema": (
        "Karim Benzema Olympique Lyonnais 2008 Ligue 1 champion",
        "Karim Benzema Real Madrid BBC Champions League 2016 2018",
        "Karim Benzema 2022 Ballon d'Or Real Madrid Champions League trophy"
    ),
    "zico": (
        "Zico Flamengo inicio da carreira 1971",
        "Zico Flamengo Campeao Libertadores Mundial 1981",
        "Zico Galinho camisa 10 Maracana lenda"
    ),

    # Music
    "drake": (
        "Drake Degrassi Jimmy Brooks Aubrey Graham 2008",
        "Drake Take Care Nothing Was the Same platinum album 2013",
        "Drake Certified Lover Boy concert tour stage"
    ),
    "playboi-carti": (
        "Playboi Carti Awful Records Magnolia 2017",
        "Playboi Carti Die Lit 2018 album",
        "Playboi Carti Whole Lotta Red King Vamp 2020"
    ),
    "lady-gaga": (
        "Lady Gaga The Fame Just Dance 2008 blonde",
        "Lady Gaga Bad Romance Born This Way 2011",
        "Lady Gaga A Star Is Born Oscar Chromatica"
    ),
    "bk": (
        "BK Castelos e Ruinas Bloco 7 2016",
        "BK Gigantes O Lider em Movimento 2018 2020",
        "BK Icarus Circo Voador show apoteose 2023"
    ),
    "asap-rocky": (
        "ASAP Rocky Live Love ASAP Peso 2011",
        "ASAP Rocky Long Live ASAP Fashion Killa",
        "ASAP Rocky Testing Dont Be Dumb Lord Flacko"
    ),
    "juice-wrld": (
        "Juice WRLD Lucid Dreams All Girls Are the Same 2018",
        "Juice WRLD Death Race for Love 2019 tour",
        "Juice WRLD Legends Never Die 999 eternal"
    ),
    "chester-bennington": (
        "Chester Bennington Linkin Park Hybrid Theory One Step Closer 2000",
        "Chester Bennington Live in Texas Meteora In the End 2003",
        "Chester Bennington Linkin Park Rock Icon Hall of Fame"
    ),
    "lalisa-manoban-lisa-rockstar": (
        "Lisa BLACKPINK debut Whistle Boombayah 2016",
        "Lalisa Manoban Lalisa Money solo breakthrough 2021",
        "Lisa Rockstar White Lotus global icon 2024"
    ),
    "daft-punk": (
        "Daft Punk Homework Da Funk unmasked 1997",
        "Daft Punk Discovery Interstella 5555 robot helmet 2001",
        "Daft Punk Random Access Memories Grammy sweep Get Lucky 2013"
    ),

    # Cinema / TV
    "seong-gi-hun-jogador-456": (
        "Seong Gi-hun Squid Game green track suit 456 red light green light",
        "Seong Gi-hun Squid Game winner suit final dinner",
        "Seong Gi-hun Squid Game Season 2 red hair revenge"
    ),

    # Anime / Game
    "jolyne-kuujou": (
        "Jolyne Cujoh Stone Ocean Green Dolphin Street prison blue",
        "Jolyne Cujoh Stone Free thread combat anime",
        "Jolyne Cujoh Stone Ocean final butterfly What a Wonderful World"
    ),
    "roxy-migurdia": (
        "Roxy Migurdia young water mage witch hat Mushoku Tensei",
        "Roxy Migurdia King class water magic staff anime",
        "Roxy Migurdia labyrinth goddess Mushoku Tensei Season 2"
    ),
    "yorha-2-gou-b-gata": (
        "2B NieR Automata black blindfold Virtuous Contract",
        "2B NieR Automata combat mode battle damage without visor",
        "2B NieR Automata Pod 042 final ending"
    ),
    "lubbock": (
        "Lubbock Akame ga Kill Night Raid green coat",
        "Lubbock Realm of the Flying Strings Cross Tail combat",
        "Lubbock Akame ga Kill final fight Syura Shambala"
    ),
    "meiko-honma": (
        "Menma Meiko Honma Anohana white dress summer ghost",
        "Menma Anohana fireworks Super Peace Busters smile",
        "Menma Anohana letter under tree final found me"
    ),
    "mitsumi-iwakura": (
        "Mitsumi Iwakura Skip and Loafer countryside rookie student",
        "Mitsumi Iwakura Skip and Loafer school festival dance Shima",
        "Mitsumi Iwakura confident student council leader"
    ),
    "kanna-kamui": (
        "Kanna Kamui Miss Kobayashi Dragon Maid cute electric tail outlet",
        "Kanna Kamui lightning magic storm Miss Kobayashi",
        "Kanna Kamui white dragon divine form sky"
    ),
}

def get_fp(path):
    if not os.path.exists(path):
        return None
    try:
        res = subprocess.run(
            ["magick", path, "-resize", "8x8!", "-colorspace", "Gray", "gray:-"],
            capture_output=True, check=True
        )
        return res.stdout
    except Exception:
        return None

def dist(fp1, fp2):
    if not fp1 or not fp2:
        return 999.0
    return sum(abs(a - b) for a, b in zip(fp1, fp2)) / len(fp1)

def search_bing_thumbs(query):
    q = query.replace(" ", "+")
    cmd = [
        "curl", "-s", "-L",
        f"https://www.bing.com/images/search?q={q}&form=HDRSC2",
        "-H", f"User-Agent: {HEADERS_CURL}"
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        html = res.stdout
        matches = re.findall(r'class="iusc"[^>]*m="([^"]+)"', html)
        results = []
        for m in matches:
            try:
                meta = json.loads(htmllib.unescape(m))
                turl = meta.get("turl")
                if turl:
                    hi_url = turl + "&w=480&h=750&c=7&rs=1"
                    results.append((meta.get("t", ""), hi_url))
            except Exception:
                pass
        return results
    except Exception:
        return []

def download_and_crop(url, out_path):
    tmp_path = out_path + ".tmp.jpg"
    cmd_curl = ["curl", "-s", "-L", url, "-o", tmp_path]
    subprocess.run(cmd_curl, check=True)
    if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) < 3000:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        return False
    # Crop and extent to 480x750 with high quality Lanczos
    cmd_magick = [
        "magick", tmp_path,
        "-filter", "Lanczos",
        "-resize", "480x750^",
        "-gravity", "center",
        "-extent", "480x750",
        "-quality", "92",
        out_path
    ]
    subprocess.run(cmd_magick, check=True)
    if os.path.exists(tmp_path):
        os.remove(tmp_path)
    return True

def process_target(slug, queries):
    q_base, q_epic, q_myth = queries
    print(f"\nProcessing {slug}...")

    base_path = os.path.join(CARDS_DIR, f"{slug}.jpg")
    epic_path = os.path.join(ERA_CACHE_DIR, f"{slug}-epic.jpg")
    myth_path = os.path.join(ERA_CACHE_DIR, f"{slug}-mythic.jpg")

    thumbs_base = search_bing_thumbs(q_base)
    time.sleep(0.2)
    thumbs_epic = search_bing_thumbs(q_epic)
    time.sleep(0.2)
    thumbs_myth = search_bing_thumbs(q_myth)
    time.sleep(0.2)

    if not thumbs_base or not thumbs_epic or not thumbs_myth:
        print(f"  WARNING: Could not fetch all thumb results for {slug} (base: {len(thumbs_base)}, epic: {len(thumbs_epic)}, myth: {len(thumbs_myth)})")
        return False

    success = False
    # Try different combinations of search results to guarantee high dist
    for i_base, (_, u_base) in enumerate(thumbs_base[:4]):
        if not download_and_crop(u_base, base_path):
            continue
        fp_b = get_fp(base_path)

        for i_epic, (_, u_epic) in enumerate(thumbs_epic[:4]):
            if not download_and_crop(u_epic, epic_path):
                continue
            fp_e = get_fp(epic_path)
            d_be = dist(fp_b, fp_e)
            if d_be < 22:
                continue

            for i_myth, (_, u_myth) in enumerate(thumbs_myth[:4]):
                if not download_and_crop(u_myth, myth_path):
                    continue
                fp_m = get_fp(myth_path)
                d_bm = dist(fp_b, fp_m)
                d_em = dist(fp_e, fp_m)

                if d_bm >= 22 and d_em >= 22:
                    success = True
                    print(f"  SUCCESS for {slug}!")
                    print(f"    Era I Base:   {thumbs_base[i_base][0][:60]}")
                    print(f"    Era II Epic:  {thumbs_epic[i_epic][0][:60]}")
                    print(f"    Era III Myth: {thumbs_myth[i_myth][0][:60]}")
                    print(f"    Distances: be={d_be:.1f}, bm={d_bm:.1f}, em={d_em:.1f}")
                    break
            if success:
                break
        if success:
            break

    if not success:
        print(f"  FAILED to achieve dist >= 22 for {slug}")
        return False
    return True

def main():
    print(f"Curating evolutionary eras for {len(TARGETS)} targets...")
    completed = 0
    failed = []
    for slug, queries in TARGETS.items():
        ok = process_target(slug, queries)
        if ok:
            completed += 1
        else:
            failed.append(slug)
        time.sleep(0.3)

    print("\n" + "="*50)
    print(f"Completed: {completed}/{len(TARGETS)}")
    if failed:
        print(f"Failed slugs: {failed}")
    else:
        print("ALL TARGETS SUCCESSFULLY PROCESSED WITH STRICT EVOLUTIONARY DISTINCTION!")

if __name__ == "__main__":
    main()
