from registration import get_connection

def setup_profiles():
    with get_connection() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS profiles (
            rku_id BIGINT PRIMARY KEY REFERENCES users(rku_id),
            display_name VARCHAR(80) NOT NULL DEFAULT '',
            company VARCHAR(120) NOT NULL DEFAULT '',
            logo_url TEXT NOT NULL DEFAULT '',
            is_public BOOLEAN NOT NULL DEFAULT FALSE
        )""")

def get_profile(rku_id, owner=False):
    with get_connection() as conn:
        row=conn.execute("SELECT display_name,company,logo_url,is_public FROM profiles WHERE rku_id=%s",(rku_id,)).fetchone()
    if not row or (not row[3] and not owner):
        return {"rku_id":rku_id,"public":False}
    return {"rku_id":rku_id,"public":row[3],"name":row[0],"company":row[1],"logo_url":row[2]}

def save_profile(rku_id, name, company, logo_url, is_public):
    with get_connection() as conn:
        conn.execute("""INSERT INTO profiles(rku_id,display_name,company,logo_url,is_public)
            VALUES(%s,%s,%s,%s,%s)
            ON CONFLICT(rku_id) DO UPDATE SET display_name=EXCLUDED.display_name,
            company=EXCLUDED.company,logo_url=EXCLUDED.logo_url,is_public=EXCLUDED.is_public""",
            (rku_id,name,company,logo_url,is_public))
    return get_profile(rku_id,True)
