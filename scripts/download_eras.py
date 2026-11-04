import json
import os
import re
import sys
import time
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

os.makedirs(".cache/era_photos", exist_ok=True)

with open("docs/catalog.json") as f:
    cards = json.load(f)

anchors = [c for c in cards if c.get("edition") == "BASIC"]

CUSTOM_QUERIES = {
    # MMA
    "alex-pereira": ("Alex Poatan Pereira Glory Kickboxing belt", "Alex Poatan Pereira UFC 300 champion belt bow"),
    "charles-do-bronx": ("Charles Oliveira UFC lightweight submission", "Charles do Bronx Oliveira UFC champion belt"),
    "anderson-silva": ("Anderson Silva Pride FC Chute Boxe", "Anderson Silva UFC Middleweight Champion Spider belt"),
    "jon-jones": ("Jon Jones UFC light heavyweight champion 2011", "Jon Jones UFC 285 Heavyweight Champion belt"),
    "khabib-nurmagomedov": ("Khabib Nurmagomedov UFC 229 Conor McGregor", "Khabib Nurmagomedov UFC 254 belt 29-0"),
    "islam-makhachev": ("Islam Makhachev UFC 280 champion belt", "Islam Makhachev UFC 302 pound for pound"),
    "israel-adesanya": ("Israel Adesanya UFC 243 champion belt", "Israel Adesanya UFC 287 knockout Pereira belt"),
    "conor-mcgregor": ("Conor McGregor UFC 194 Jose Aldo", "Conor McGregor UFC 205 champ champ two belts"),
    "ilia-topuria": ("Ilia Topuria UFC 298 Alexander Volkanovski", "Ilia Topuria UFC featherweight champion belt"),
    "alex-volkanovski": ("Alexander Volkanovski UFC 245 Max Holloway", "Alexander Volkanovski UFC champion belt"),
    "dustin-poirier": ("Dustin Poirier UFC lightweight interim belt", "Dustin Poirier BMF UFC knockout"),
    "justin-gaethje": ("Justin Gaethje UFC interim champion", "Justin Gaethje BMF belt knockout"),
    "max-holloway": ("Max Holloway UFC 212 Jose Aldo belt", "Max Holloway UFC 300 BMF knockout"),
    "sean-omalley": ("Sean O'Malley UFC 292 Aljamain Sterling", "Sean O'Malley UFC bantamweight champion belt"),
    "georges-st-pierre": ("Georges St-Pierre UFC welterweight champion", "Georges St-Pierre UFC 217 middleweight champion"),
    "demetrious-johnson": ("Demetrious Johnson UFC flyweight champion 11 defenses", "Demetrious Johnson ONE Championship belt flying knee"),
    "fedor-emelianenko": ("Fedor Emelianenko Pride FC Heavyweight Champion", "Fedor Emelianenko Bellator retirement legend"),
    "francis-ngannou": ("Francis Ngannou UFC 260 Stipe Miocic belt", "Francis Ngannou PFL heavyweight champion belt"),
    "stipe-miocic": ("Stipe Miocic UFC heavyweight champion 2016", "Stipe Miocic UFC heavyweight record defenses"),
    "ronda-rousey": ("Ronda Rousey UFC 157 first champion armbar", "Ronda Rousey UFC women bantamweight belt Hall of Fame"),
    "amanda-nunes": ("Amanda Nunes UFC 200 Miesha Tate belt", "Amanda Nunes UFC double champion two belts GOAT"),
    "zhang-weili": ("Zhang Weili UFC 248 Joanna Jedrzejczyk", "Zhang Weili UFC strawweight champion belt"),
    "valentina-shevchenko": ("Valentina Shevchenko UFC flyweight champion belt", "Valentina Shevchenko UFC title defense bullet"),
    "wanderlei-silva": ("Wanderlei Silva Pride FC Middleweight Champion", "Wanderlei Silva The Axe Murderer Chute Boxe"),
    "vitor-belfort": ("Vitor Belfort UFC 12 Heavyweight Tournament", "Vitor Belfort TRT head kick UFC"),
    "royce-gracie": ("Royce Gracie UFC 1 kimono Gi", "Royce Gracie UFC Hall of Fame legend"),
    "nate-diaz": ("Nate Diaz UFC 196 Conor McGregor submission", "Nate Diaz 209 Stockton slap UFC"),

    # Football
    "lionel-messi": ("Lionel Messi Barcelona 2015 Champions League MSN", "Lionel Messi World Cup 2022 trophy Argentina golden ball"),
    "cristiano-ronaldo": ("Cristiano Ronaldo Manchester United 2008 Ballon d'Or", "Cristiano Ronaldo Real Madrid Champions League 2017 trophy"),
    "neymar-jr": ("Neymar Jr Santos FC Libertadores 2011", "Neymar Jr Barcelona Champions League 2015 MSN"),
    "pele": ("Pele Santos FC 1962 Intercontinental", "Pele 1970 World Cup trophy Brazil King"),
    "ronaldo-fenomeno": ("Ronaldo Fenomeno Barcelona 1997 Inter", "Ronaldo Nazario 2002 World Cup trophy Brazil 8 goals"),
    "ronaldinho-gaucho": ("Ronaldinho Gaucho Barcelona Ballon d'Or 2005", "Ronaldinho Brazil 2002 World Cup champion"),
    "diego-maradona": ("Diego Maradona Boca Juniors Barcelona", "Diego Maradona World Cup 1986 trophy Napoli"),
    "zinedine-zidane": ("Zinedine Zidane Juventus 1998 World Cup", "Zinedine Zidane Real Madrid 2002 volley Champions League"),
    "zico": ("Zico Flamengo 1981 Libertadores Mundial", "Zico Galinho Flamengo camisa 10"),
    "romario": ("Romario Barcelona 1994 Dream Team", "Romario World Cup 1994 trophy Brazil Baixinho"),
    "kaka": ("Kaka AC Milan 2007 Ballon d'Or Champions League", "Kaka Milan Real Madrid"),
    "kylian-mbappe": ("Kylian Mbappe Monaco 2017 World Cup 2018", "Kylian Mbappe Real Madrid 2024 France"),
    "vini-jr": ("Vinicius Junior Real Madrid 2022 Champions League goal", "Vini Jr Real Madrid 2024 Champions League trophy"),
    "erling-haaland": ("Erling Haaland Borussia Dortmund Champions League", "Erling Haaland Manchester City Treble Premier League trophy"),
    "jude-bellingham": ("Jude Bellingham Borussia Dortmund 2023", "Jude Bellingham Real Madrid Champions League trophy 2024"),
    "lamine-yamal": ("Lamine Yamal Barcelona 2024", "Lamine Yamal Euro 2024 champion Spain trophy"),

    # Basketball
    "michael-jordan": ("Michael Jordan Chicago Bulls 1991 first championship", "Michael Jordan 1998 The Last Dance 6 rings trophy"),
    "lebron-james": ("LeBron James Miami Heat 2012 champion MVP", "LeBron James 2020 Lakers trophy scoring king all time"),
    "kobe-bryant": ("Kobe Bryant number 8 three peat Lakers", "Kobe Bryant number 24 2010 NBA Finals MVP trophy"),
    "stephen-curry": ("Stephen Curry 2015 2016 73-9 unanimous MVP", "Stephen Curry 2022 NBA Finals MVP trophy 4 rings"),
    "shaquille-oneal": ("Shaquille O'Neal Orlando Magic rookie dunk", "Shaquille O'Neal Lakers three peat Finals MVP trophy"),
    "giannis-antetokounmpo": ("Giannis Antetokounmpo 2019 2020 MVP", "Giannis Antetokounmpo 2021 NBA Finals trophy 50 points"),
    "allen-iverson": ("Allen Iverson 2001 MVP step over Tyronn Lue", "Allen Iverson Philadelphia 76ers Hall of Fame"),
    "luka-doncic": ("Luka Doncic Real Madrid EuroLeague MVP", "Luka Doncic Dallas Mavericks NBA Finals 2024"),
    "nikola-jokic": ("Nikola Jokic Denver Nuggets back to back MVP", "Nikola Jokic 2023 NBA Finals MVP trophy champion"),

    # Music / Idols
    "eminem": ("Eminem The Marshall Mathers LP 2000", "Eminem Rap God Hall of Fame 2022"),
    "2pac": ("2Pac All Eyez on Me Death Row 1996", "Tupac Shakur Makaveli The Don Killuminati"),
    "notorious-big": ("The Notorious BIG Ready to Die 1994", "Biggie Smalls Life After Death King of New York"),
    "michael-jackson": ("Michael Jackson Thriller 1982 red jacket", "Michael Jackson Billie Jean Moonwalk HIStory World Tour"),
    "matue": ("Matue 333 Quer Voar 2021", "Matue Plantao Festival King of Trap 2024"),
    "travis-scott": ("Travis Scott Rodeo Antidote 2015", "Travis Scott Astroworld Utopia Circus Maximus"),
    "post-malone": ("Post Malone Beerbongs & Bentleys 2018", "Post Malone Hollywood Bleeding Austin"),
    "the-weeknd": ("The Weeknd Starboy 2016", "The Weeknd After Hours red suit Super Bowl 2021"),
    "freddie-mercury": ("Freddie Mercury Queen Live at Wembley 1986", "Freddie Mercury Live Aid 1985 iconic yellow jacket"),

    # Cinema / TV
    "batman-dc": ("Batman The Dark Knight Christian Bale", "Batman Hellbat armor DC Comics Justice League"),
    "iron-man-marvel": ("Iron Man Mark 3 Robert Downey Jr 2008", "Iron Man Mark 85 Nano Gauntlet I am Iron Man Endgame"),
    "darth-vader-star-wars": ("Darth Vader Revenge of the Sith Anakin", "Darth Vader Return of the Jedi Rogue One hall scene"),
    "thanos-marvel": ("Thanos Infinity War Infinity Gauntlet snap", "Thanos Endgame dual blade armor balance"),
    "thor-marvel": ("Thor Ragnarok lightning eyes dual swords", "Thor Infinity War Stormbreaker Bring me Thanos"),
    "neo-matrix": ("Neo The Matrix 1999 lobby shootout", "Neo The Matrix Revolutions flying The One"),
    "john-wick-cinema": ("John Wick chapter 2 continental", "John Wick chapter 4 stairs Paris duel"),

    # Anime / Manga
    "son-goku": ("Son Goku Super Saiyan Blue Kaioken", "Son Goku Mastered Ultra Instinct silver hair"),
    "goku-ultra-instinct": ("Son Goku Super Saiyan Blue Kaioken", "Son Goku Mastered Ultra Instinct silver hair"),
    "monkey-d-luffy": ("Monkey D Luffy Gear 4 Boundman Wano", "Monkey D Luffy Gear 5 Sun God Nika anime"),
    "luffy-gear-5": ("Monkey D Luffy Gear 4 Boundman Wano", "Monkey D Luffy Gear 5 Sun God Nika anime"),
    "roronoa-zoro": ("Roronoa Zoro Enma Wano", "Roronoa Zoro King of Hell Asura anime"),
    "zoro-roronoa": ("Roronoa Zoro Enma Wano", "Roronoa Zoro King of Hell Asura anime"),
    "satoru-gojou": ("Satoru Gojo Hidden Inventory teen", "Satoru Gojo Unlimited Void Hollow Purple anime"),
    "sukuna": ("Ryomen Sukuna Yuuji Malevolent Shrine domain", "Ryomen Sukuna Heian Era True Form original four arms"),
    "sung-jinwoo": ("Sung Jinwoo Igris Shadow Monarch", "Sung Jinwoo True Shadow Monarch Ashborn purple"),
    "jin-u-seong": ("Sung Jinwoo Igris Shadow Monarch", "Sung Jinwoo True Shadow Monarch Ashborn purple"),
    "naruto-uzumaki": ("Naruto Uzumaki Six Paths Sage Mode Kurama", "Naruto Uzumaki Baryon Mode Boruto"),
    "sasuke-uchiha": ("Sasuke Uchiha Mangekyou Sharingan Susanoo", "Sasuke Uchiha Rinnegan Perfect Susanoo"),
    "ichigo-kurosaki": ("Ichigo Kurosaki Vasto Lorde Hollow mask", "Ichigo Kurosaki Horn of Salvation True Bankai TYBW"),
    "tanjirou-kamado": ("Tanjiro Kamado Hinokami Kagura dance", "Tanjiro Kamado 13th form Sun Breathing Demon Slayer"),
    "killua-zoldyck": ("Killua Zoldyck Godspeed Kanmuru", "Killua Zoldyck Whirlwind lightning assassin aura"),
    "gon-freecss": ("Gon Freecss Jajanken Chimera Ant", "Gon Freecss Adult transformation long hair Nen"),
    "eren-yeager": ("Eren Yeager Attack Titan War Hammer Season 4", "Eren Yeager Founding Titan Rumbling"),
    "levi": ("Levi Ackerman Season 3 Beast Titan", "Levi Ackerman vs Beast Titan thunder spears"),
    "saitama": ("Saitama serious punch One Punch Man", "Saitama serious punch cosmic Garou table flip"),
    "dio-brando": ("Dio Brando Phantom Blood vampire mask", "DIO The World JoJo Stardust Crusaders awakened"),
    "asuka-langley-souryuu": ("Asuka Langley Evangelion Unit 02 red", "Asuka Langley Shikinami The End of Evangelion eyepatch"),
    "edward-elric": ("Edward Elric Fullmetal Alchemist automail transmutation", "Edward Elric God transmutation alchemy final"),
    "rei-ayanami": ("Rei Ayanami Evangelion Unit 00 plugsuit", "Rei Ayanami Lilith Giant Third Impact"),
    "guts": ("Guts Golden Age mercenary sword", "Guts Berserker Armor Dragonslayer Eclipse"),
    "l-lawliet": ("L Lawliet Death Note sitting chair cake", "L Lawliet Death Note rain rooftop Bell scene"),
    "shinji-ikari": ("Shinji Ikari Evangelion Unit 01 plugsuit", "Shinji Ikari Evangelion Unit 01 awakened Third Impact"),
    "yuuji-itadori": ("Yuji Itadori Black Flash Jujutsu Kaisen", "Yuji Itadori Soul Dismantle Sukuna final fight"),
}

def get_queries(c):
    slug = c['slug']
    if slug in CUSTOM_QUERIES:
        return CUSTOM_QUERIES[slug]
    clean_name = re.sub(r'\s*\(.*?\)\s*', ' ', c['name']).strip()
    series = c.get('seriesTitle') or ''
    niche = c.get('niche') or ''
    if niche == 'sport_mma':
        return (f"{clean_name} UFC fighter octagon", f"{clean_name} UFC champion belt")
    if niche == 'sport_football':
        return (f"{clean_name} football match celebration", f"{clean_name} champion trophy celebration")
    if niche == 'sport_basketball':
        return (f"{clean_name} NBA dunk basketball", f"{clean_name} NBA Finals trophy champion")
    if niche.startswith('music_') or niche == 'idol':
        return (f"{clean_name} singer concert live", f"{clean_name} iconic award photoshoot")
    if niche == 'cinema_tv':
        return (f"{clean_name} {series} movie scene", f"{clean_name} {series} iconic poster")
    if niche == 'game':
        return (f"{clean_name} {series} battle", f"{clean_name} {series} ultimate form")
    # anime default
    return (f"{clean_name} {series} anime fight", f"{clean_name} {series} awakened ultimate power")

def ddg_search_thumbs(query, retries=2):
    for attempt in range(retries):
        try:
            url = f"https://duckduckgo.com/?q={urllib.parse.quote(query)}&iax=images&ia=images"
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8"
            })
            html = urllib.request.urlopen(req, timeout=8).read().decode("utf-8", errors="ignore")
            m = re.search(r'vqd=([\d-]+)', html) or re.search(r'vqd=[\"\']([\d-]+)[\"\']', html)
            if not m:
                time.sleep(0.5)
                continue
            vqd = m.group(1)
            api_url = f"https://duckduckgo.com/i.js?l=us-en&o=json&q={urllib.parse.quote(query)}&vqd={vqd}&f=,,,&p=1"
            req2 = urllib.request.Request(api_url, headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://duckduckgo.com/"
            })
            data = json.loads(urllib.request.urlopen(req2, timeout=8).read().decode("utf-8"))
            return [r.get("thumbnail") for r in data.get("results", []) if r.get("thumbnail")]
        except Exception:
            time.sleep(0.5)
    return []

def download_card_eras(c):
    slug = c['slug']
    epic_path = f".cache/era_photos/{slug}-epic.jpg"
    mythic_path = f".cache/era_photos/{slug}-mythic.jpg"
    base_asset = f"docs/assets/cards/{slug}.jpg"
    base_data = None
    if os.path.exists(base_asset):
        try:
            with open(base_asset, "rb") as bf:
                base_data = bf.read()
        except Exception:
            pass

    has_epic = os.path.exists(epic_path) and os.path.getsize(epic_path) > 3000
    has_mythic = os.path.exists(mythic_path) and os.path.getsize(mythic_path) > 3000
    if has_epic and has_mythic:
        return True

    q_epic, q_mythic = get_queries(c)
    t1 = ddg_search_thumbs(q_epic)
    time.sleep(0.15)
    t2 = ddg_search_thumbs(q_mythic)
    time.sleep(0.15)

    thumbs = []
    for t in t1[:4] + t2[:5] + t1[4:]:
        if t and t not in thumbs:
            thumbs.append(t)

    if len(thumbs) < 2:
        clean_name = re.sub(r'\s*\(.*?\)\s*', ' ', c['name']).strip()
        series = c.get('seriesTitle') or ''
        fallback = ddg_search_thumbs(f"{clean_name} {series}")
        for t in fallback:
            if t and t not in thumbs:
                thumbs.append(t)

    saved_epic = has_epic
    saved_mythic = has_mythic

    for t in thumbs:
        if saved_epic and saved_mythic:
            break
        try:
            hi_url = t + "&w=480&h=750&c=7&rs=1"
            req = urllib.request.Request(hi_url, headers={"User-Agent": "Mozilla/5.0"})
            data = urllib.request.urlopen(req, timeout=8).read()
            if len(data) < 3000:
                continue
            # Verifica se não é idêntico à base
            if base_data and data == base_data:
                continue
            if not saved_epic:
                with open(epic_path, "wb") as f_out:
                    f_out.write(data)
                saved_epic = True
            elif not saved_mythic:
                # Verifica se não é idêntico ao epic
                with open(epic_path, "rb") as f_ep:
                    if f_ep.read() == data:
                        continue
                with open(mythic_path, "wb") as f_out:
                    f_out.write(data)
                saved_mythic = True
        except Exception:
            continue

    return saved_epic and saved_mythic

if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else len(anchors)
    target_anchors = anchors[:limit]
    print(f"Starting era photos download for {len(target_anchors)} anchors...")
    success = 0
    with ThreadPoolExecutor(max_workers=5) as ex:
        for res in ex.map(download_card_eras, target_anchors):
            if res:
                success += 1
    print(f"Completed: {success}/{len(target_anchors)} anchors ready in .cache/era_photos.")
