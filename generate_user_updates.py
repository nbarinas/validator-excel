import pandas as pd
import io

raw_data = """Nombre	cedula 	celular	Barrio	Direccion	Entidad Bancaria 	Nuemro 	tipo de cuenta 	titular de la cuenta
Andrea Enciso	53016780	3219502691	CARRERA 65 57 - 33 SUR	VILLA DEL RIO	Nequi	3219502691	ahorro	Maria Andrea Enciso
Andres Rivas	13050271	3237332804	NO LA SABE	FUSAGASUFA				
Brayan Roncancio	1074160628	31134782763		el angulo	Caja Social	24131596502	ahorro	Brayan Rocancio
Camila Montañez	1000931469	3227828125	cll 40 i sur # 12 i 20	san miguel	Caja Social	24131852567	ahorro	Camila Momntañez
Cesar Cruz	80119682	3506008846	CRA 14 ESTE # 42 C -36	LA VICTORIA	Caja Social	24131598027	ahorro	Cesar Cruz
Cesar Gutierrez	19120907	3133730153	CLL 32 51-53 SUR	ALCALA	Nequi	3133730153	ahorro	Cesar Gutierrez
Chelovay Cruz	1120838342	3208695323	CRA 8 # 32-70 SUR	SAN ISIDRO	Nequi	3208695323	ahorro	Chelo Cruz
Daniel Arévalo	10110848897	3223623685	CLL 71 SUR #98 B - 50	BOSA RECREO	Nequi	3168552434	ahorro	Ana Arevalo
Daniel Corea	1016834271		cll 39 c bis f sur 16	talavera	Caja Social	24143623678	ahorro	Titto Correo
Fernanda Ramos	37441290	3017793350	CR 81 B # 51 07 SUR	BRITALIA	Caaja Social	24132834649	ahorro	Fernanda Ramos
Fernanda Ramos	37441290	3017793350	CRA 81 B # 51 -07	BRITALIA	Caja Social	24132834649	ahorro	Fernanda Ramos
Freddy Guarin	19435786	3183703074	CLL 52 # 9 -58	CHAPINERO	Nequi	3183703074	ahorro	Freddy Guarin
Fredy Guarin	19435786	3183703074	CALLE 52 A # 9-26 APTO 201	CHAPINERO	Nequi	3183703074	ahorro	Fredy Guarin
Gabriela Huertas	101313992	3013807350	CLL 71 SUR #98 B - 50	BOSA RECREO	Nequi	3194653470	ahorro	Laura Huertas
German Camargo	19393745	3213737132	CRA 12 F # 19 - 23 SUR	CIUDAD JARDIN	Davivienda	474600016353	ahorro	German Camargo
German Camargo	19393745	3213737132	CR 12 F 19 23	CIUDAD JARDIN SU7R	Davivienda	274600016353	ahorro	German Camargo
Giovanny Rubiano	10142262994	3107846661	cll 68 a # 49 c 26 sur	candelaroa la nueva	Caja Social	24081370177	ahorro	Caja Social
Giovanny Rubiano	79736431	3107846661	Calle 68 A # 49 C - 26 Sur	Candelaria la nueva	Caja Social	24081370177	ahorro	Giovanny Rubiano
Hector Rincon	79575484	3143250427	cr 68 d bi 39 c 73 sur	talavera	Caja Social	24100111572	ahorro	Hectir Rincon
Íngrid Cordoba	1033719163	3203121920	NO LA SABE	CIUDAD VERDE	Caja Social	24131700248	ahorro	Ingrid Cordoba
Ingrid Romero	39095581	3001846907	cr 93 b # 34 15 sur	la rivera	Cja Social	24131710409	ahorro	Ingrid Romero
Isaac Palacios	79301254		CRA 96 # 42B - 55 Sur	PATIO BONITO	Caja Social	24133059775	ahorro	Isaac Palacios
Isadora Arguelles	5209015	3002398045	cr 36 este 38 a 10	los pinos	Caja Soaol	24131317639	ahorro	Isadora Arguelles
Isadora Arguelles	308100	3002398045	cr 36 este 38 a 10	los pinoa	Caja Social	24131317639	ahorro	Isadora Arguelles
Jacob Pacheco	ppt 517656376	3148449086	vive en hotel por el moenmto		Nequi	3148449086	ahorro	Jacob Pacheco
Jairo Rodriguez	19368245	3114908979	CLL 71 SUR # 97 C -50	BOSA RECREO	Caja Social	24030586633	ahorro	Jairo Rodriguez
Jairo Rodriguez	19368245				Caja Social	24030586633	ahorro	Jairo Rodriguez
Javier Rincon	79575484	3171911734	carrera 68 d bis 39 c 73 sur	talavera	Caja Social	24100111572	ahorro	Hectir Rincon
Jesica Ardila	1030647401	3223839000	dg 43 # 20 54 sur	santa lucia	Csaja Socxial	24126183872	ahorro	Johana Pinzon
Johana Pinzon	1033817278	3232505024	carrera 4 g # 52a 50 sur	la paz	Csaja Socxial	24126183872	ahorro	Johana Pinzon
Juan Moreno	1021666357	3222813121	cll 43 sur $ 3 52 este	san miguel	Caja Social	24142559673	ahorro	Juan Moreno
Juliana Bohorquez	1022945257					3108172039	ahorro	
Kevin Sanchez	1024469763	3016828438	DIAGONAL 68 B # 28 - 21 SUR	VILLA CANDELARIA	Caja Social	24131035944	ahorro	Keviin Sanchez
Laura Borja	1021395763	3026337510	Carrera 19 A # 19 b - 194 Sur	Hogares Soacha	Nequi	3026337510	ahorro	Laura Borja
Lorena Cubillos	1001058334	3102382305	dg 46 sur 13 j 10	san jorge		24150177166	ahorro	Ilce Cubillos
Luz Marina Diaz	51592026	3118682910	CLL 23 G BIS A # 96 F-06	FONTIBON COFRADIA	Nequi	3118682910	ahorro	Luz Marina Diaz
Luz Marina Diaz	51592026	3118682910	CALLE 23 G BIS A # 96 F - 06	COFRADIA FONTIVON	Nequi	3118682910	ahorro	Luz Marina Lizarazo
Marcela Bautista	52185901		CRA 64 #67 D-38	SAN FERNANDO	Caja Social	24110859655	ahorro	Marcela Bautista
Maria Teresa Rueda	32782701	3013322314	cll 55 sur # 100 06	bosa porvenir	Caja Social	24121073994	ahorro	Maria Teresa Rueda
Marisol Dasa	36301865	36301865	ciudad verde	cpjinto malva	Caja Social	24087436619	ahorro	Cajja Social
Mattha Albarracin			cll 78 c 14 c 44 int 1	marichuela	Caja Social	24077357113	ahorro	Martha Albarracin
Miryam Leon	51706398	3118991344	CLL 71 SUR # 97 C -50	BOSA RECREO	Caja Social	24030586633	ahorro	Jairo Rodriguez
Natalia Cepeda	1031132391	3143334981	tras 15 a bus # 94 14 sur	san gorge	Caja Social	24131856785	ahorro	Natalia Cepeda
Nubia Garcia	51605052	3118880055	cll 59 a sur $ 75 h 18	estabncua	Caja Social	24131630868	ahorro	Nubia Garcia
Oscar Benitez	1018497499	3011805519	CLL 86 A # 80 K 40 SUR	PORTALES D ESAN JOSE INTEROIOR 29	Caja Social	24143146847	ahorro	Oscar Benitez
Sandra Dominguez	52526761	3172624804	CR 68 F # 3 71 SUR	FLORESTA SUR	Caja Social	24144026528	ahorro	Sandra Dominguez
Sarey Molina	1021674138	3134886627	Carrera 16 Este # 48 - 34 Sur	Gaviotas	Caja Social	24147694379	ahorro	Sarey Molina
Tito Correa	80218018	3115852931	CLL 39 C BIS SUR # 68 F -16	TALAVERA	Caja Social	24143623678	ahorro	Tito Correa
Johana Benitez		3203513376						
Milena Zarate	51155850	3173852676	carrera 1 H # 37 38 sur	Guacamayas	Caja Social	24150874791		Milena Zarate
Cristian Gonzales	1021668527	3136139581	carrera 1 H # 37 38 sur	Guacamayas	Caja Social	24131634783		Cristian Gonzales
Esteban Cruz		3229505926						
Yraima Coromoto Rey	ppt 63502232	3113232015			Caja Social	24131693852		Yraima Coromoto Rey
Caleb Cubillos		3134870394						
Karol Correa	1022437903	3027492497			Caja Social	24066834278		Karol Correa
Andres Leal		3229457640			Daviplata	3229457640		Andres Leal
Damiana Garcia		3018607969			Nequi	3204934355		Damiana
Nicolas Galindo		3205524385						
Andrea Colmenares		3223182966						
Sandra Benitez	52507637	3158160379			Caja Social	24072602281		Sandra Benitez
Mariana Gomez	1026287682	3166044739			Caja Social	24131596502		Mariana Gomez
"""

# Simulate reading tab separated
try:
    df = pd.read_csv(io.StringIO(raw_data), sep='\t', header=0)
except:
    # Fallback if separator issues
    df = pd.read_csv(io.StringIO(raw_data), sep='\t', header=0, on_bad_lines='skip')

# Normalize columns
df.columns = [c.strip().lower() for c in df.columns]
# Expected: nombre, cedula, celular, barrio, direccion, entidad bancaria, nuemro, tipo de cuenta, titular de la cuenta

# Mappings (Input -> DB Field)
# DB table: users
# Fields: full_name, username (optional?), address, neighborhood, bank, account_number, account_type, account_holder
field_map = {
    "nombre": "full_name",
    "barrio": "neighborhood",
    "direccion": "address",
    "entidad bancaria": "bank",
    "nuemro": "account_number",
    "tipo de cuenta": "account_type",
    "titular de la cuenta": "account_holder",
    "cedula": "username" 
}

# Generate SQL
sql_statements = []

for _, row in df.iterrows():
    phone = str(row.get('celular', '')).strip()
    
    # Needs valid phone
    if not phone or phone.lower() == 'nan' or phone == '':
        continue
    
    # Handle weird chars in phone '31134782763' might be typo?
    # Strip decimals .0
    if phone.endswith('.0'): phone = phone[:-2]
        
    updates = []
    
    def clean(val):
        s = str(val).strip()
        if s.lower() == 'nan' or s == '': return None
        return s.replace("'", "''") # Escape quotes

    for col, db_field in field_map.items():
        if col in df.columns:
            val = clean(row[col])
            
            # Special case: don't update username if empty, or if we want to be careful
            if db_field == "username":
                continue # Skip username update for safety unless explicitly requested? No, usually safer to skip in bulk by phone.
            
            if val:
                updates.append(f"{db_field} = '{val}'")
    
    if updates:
        # Create Update statement
        sql = f"UPDATE users SET {', '.join(updates)} WHERE phone_number LIKE '%{phone}%';"
        sql_statements.append(sql)

# Output
output_file = "update_users_by_phone.sql"
with open(output_file, "w", encoding="utf-8") as f:
    f.write("-- Generated SQL Updates based on Phone Number Match\n")
    f.write("\n".join(sql_statements))

print(f"Generated {len(sql_statements)} statements in {output_file}")
