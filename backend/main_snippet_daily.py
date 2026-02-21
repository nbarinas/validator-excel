@app.get("/reports/daily-effectives")
def get_daily_effectives(
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Get count of effective calls (managed/efectiva_campo) for TODAY.
    Grouped by Study and Agent.
    """
    # Use raw SQL for simplicity and performance with grouping
    from sqlalchemy import text
    
    # Adjust timezone to Colombia (UTC-5)
    # If server is UTC, we want calls where valid_date >= today_start
    # For simplicity, we'll trust realization_date is stored correctly or just check updated_at/status change
    # Queries "managed" or "efectiva_campo"
    
    # We want: Study Name, Agent Name, Count
    
    sql = text("""
        SELECT 
            s.name as study_name,
            u.full_name as agent_name,
            u.username as agent_username,
            COUNT(*) as count
        FROM calls c
        JOIN users u ON c.agent_id = u.id
        JOIN studies s ON c.study_id = s.id
        WHERE 
            (c.status = 'managed' OR c.status = 'efectiva_campo')
            AND DATE(c.updated_at) = CURRENT_DATE
        GROUP BY s.name, u.full_name, u.username
        ORDER BY s.name, count DESC
    """)
    
    # Note: SQLite 'CURRENT_DATE' works. Postgres/MySQL might differ.
    # If using MySQL: DATE(c.updated_at) = CURDATE()
    # Let's try uniform approach or Python filtering if DB is uncertain.
    # Given user has "MySQL" in comments, we should use MySQL syntax or generic.
    # MySQL: DATE(updated_at) = CURDATE()
    # SQLite: date(updated_at) = date('now')
    
    # Safest is to pass today's date from Python
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    # Improved SQL for compatibility (Parameterized)
    sql = text("""
        SELECT 
            s.name as study_name,
            u.full_name as agent_name,
            u.username as agent_username,
            COUNT(*) as count
        FROM calls c
        JOIN users u ON c.agent_id = u.id
        JOIN studies s ON c.study_id = s.id
        WHERE 
            (c.status = 'managed' OR c.status = 'efectiva_campo')
            AND c.updated_at >= :today_start
            AND c.updated_at < :tomorrow_start
        GROUP BY s.name, u.full_name, u.username
        ORDER BY s.name, count DESC
    """)
    
    start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    
    result = db.execute(sql, {"today_start": start, "tomorrow_start": end}).fetchall()
    
    data = []
    current_study = None
    study_data = None
    
    # Transform to nested structure for frontend:
    # [ { study: "A", agents: [ {name: "Pepe", count: 5}, ... ] }, ... ]
    
    # Since it's ordered by study_name, we can just iterate
    tree = {}
    
    for row in result:
        # row is tuple-like or object-like depending on driver
        # TextClause usually returns tuples or RowProxy
        s_name = row[0] # study_name
        a_name = row[1] or row[2] # full_name or username
        cnt = row[3]
        
        if s_name not in tree:
            tree[s_name] = []
        
        tree[s_name].append({"name": a_name, "count": cnt})
        
    # Convert to list
    output = []
    for s_name, agents in tree.items():
        output.append({
            "study_name": s_name,
            "agents": agents,
            "total": sum(a['count'] for a in agents)
        })
        
    return output
