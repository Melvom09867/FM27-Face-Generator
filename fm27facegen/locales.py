"""Übersetzungen. Jede Zeile: (Deutsch, Englisch, Italienisch, Französisch, Spanisch, Portugiesisch, Japanisch, Koreanisch).

Neue Texte immer in allen 8 Sprachen ergänzen – ein Test prüft das.
"""

# fmt: off
STRINGS: dict[str, tuple[str, ...]] = {
    # ------------------------------------------------------------------ Sprachdialog
    "lang.title": ("Sprache wählen", "Choose language", "Scegli la lingua", "Choisir la langue", "Elegir idioma", "Escolher idioma", "言語を選択", "언어 선택"),
    "lang.label": ("Sprache:", "Language:", "Lingua:", "Langue :", "Idioma:", "Idioma:", "言語:", "언어:"),
    "lang.dont_ask": ("Beim Start nicht mehr fragen", "Don't ask again at startup", "Non chiedere più all'avvio", "Ne plus demander au démarrage", "No volver a preguntar al iniciar", "Não perguntar novamente ao iniciar", "次回から起動時に確認しない", "다음부터 시작할 때 묻지 않기"),
    "btn.ok": ("OK", "OK", "OK", "OK", "Aceptar", "OK", "OK", "확인"),
    "btn.language": ("Sprache", "Language", "Lingua", "Langue", "Idioma", "Idioma", "言語", "언어"),
    "msg.lang_busy": ("Die Sprache kann gewechselt werden, sobald die aktuelle Erzeugung fertig ist.", "The language can be changed once the current generation has finished.", "La lingua può essere cambiata al termine della generazione in corso.", "La langue pourra être changée une fois la génération en cours terminée.", "El idioma se puede cambiar cuando termine la generación actual.", "O idioma pode ser alterado quando a geração atual terminar.", "現在の生成が終わってから言語を変更できます。", "현재 생성이 끝나면 언어를 변경할 수 있습니다."),

    # ------------------------------------------------------------------ Tabs
    "tab.player": ("Spieler", "Player", "Giocatore", "Joueur", "Jugador", "Jogador", "選手", "선수"),
    "tab.look": ("Aussehen", "Look", "Aspetto", "Apparence", "Aspecto", "Aparência", "外見", "외모"),
    "tab.personality": ("Persönlichkeit", "Personality", "Personalità", "Personnalité", "Personalidad", "Personalidade", "性格", "성격"),
    "tab.output": ("Ausgabe", "Output", "Output", "Sortie", "Salida", "Saída", "出力", "출력"),
    "tab.ai": ("KI", "AI", "IA", "IA", "IA", "IA", "AI", "AI"),
    "tab.gallery": ("Galerie", "Gallery", "Galleria", "Galerie", "Galería", "Galeria", "ギャラリー", "갤러리"),
    "tab.list": ("Spielerliste (FM-Import)", "Player list (FM import)", "Lista giocatori (import FM)", "Liste de joueurs (import FM)", "Lista de jugadores (importar FM)", "Lista de jogadores (importar FM)", "選手リスト（FMから読込）", "선수 목록 (FM 가져오기)"),

    # ------------------------------------------------------------------ Tab Spieler
    "lbl.country": ("Geburtsland", "Country of birth", "Paese di nascita", "Pays de naissance", "País de nacimiento", "País de nascimento", "出生国", "출생 국가"),
    "hint.country": ("Tippen zum Suchen. Bestimmt die typische Herkunft.", "Type to search. Determines the typical background.", "Digita per cercare. Determina l'origine tipica.", "Tapez pour rechercher. Détermine l'origine typique.", "Escribe para buscar. Determina el origen típico.", "Digite para pesquisar. Define a origem típica.", "入力して検索。典型的な出自を決めます。", "입력하여 검색. 대표적인 출신을 결정합니다."),
    "lbl.second": ("Herkunft Eltern", "Parents' origin", "Origine genitori", "Origine des parents", "Origen de los padres", "Origem dos pais", "両親の出身", "부모의 출신"),
    "hint.second": ("Optional, z. B. Geburtsland Deutschland + Eltern aus Ghana. '—' = keine zweite Herkunft.", "Optional, e.g. born in Germany + parents from Ghana. '—' = no second origin.", "Facoltativo, ad es. nato in Germania + genitori dal Ghana. '—' = nessuna seconda origine.", "Facultatif, p. ex. né en Allemagne + parents du Ghana. « — » = pas de seconde origine.", "Opcional, p. ej. nacido en Alemania + padres de Ghana. '—' = sin segundo origen.", "Opcional, ex.: nascido na Alemanha + pais de Gana. '—' = sem segunda origem.", "任意。例：ドイツ生まれ＋両親がガーナ出身。「—」＝第二の出身なし。", "선택 사항. 예: 독일 출생 + 부모는 가나 출신. '—' = 두 번째 출신 없음."),
    "lbl.parents": ("Eltern", "Parents", "Genitori", "Parents", "Padres", "Pais", "両親", "부모"),
    "hint.parents": ("'Beide Eltern': Aussehen wie im Herkunftsland. 'Ein Elternteil': gemischt aus beiden Ländern.", "'Both parents': looks like the parents' country. 'One parent': mixed from both countries.", "'Entrambi i genitori': aspetto come nel paese d'origine. 'Un genitore': misto tra i due paesi.", "« Les deux parents » : apparence du pays d'origine. « Un parent » : mélange des deux pays.", "'Ambos padres': aspecto del país de origen. 'Un progenitor': mezcla de ambos países.", "'Ambos os pais': aparência do país de origem. 'Um dos pais': mistura dos dois países.", "「両親とも」：両親の国の外見。「片親」：両国のミックス。", "'부모 모두': 부모 국가의 외모. '부모 중 한 명': 두 나라의 혼혈."),
    "lbl.ethnicity": ("Ethnie", "Ethnicity", "Etnia", "Ethnie", "Etnia", "Etnia", "民族", "민족"),
    "lbl.gender": ("Geschlecht", "Gender", "Sesso", "Sexe", "Sexo", "Sexo", "性別", "성별"),
    "lbl.age": ("Alter", "Age", "Età", "Âge", "Edad", "Idade", "年齢", "나이"),
    "word.to": (" bis ", " to ", " a ", " à ", " a ", " a ", " ～ ", " ~ "),
    "word.years": (" Jahre", " years", " anni", " ans", " años", " anos", " 歳", " 세"),
    "hint.age": ("FM-Jugendspieler kommen meist mit 15–16 Jahren. Bei einem Bereich wird je Bild zufällig gewählt.", "FM youth players usually arrive aged 15–16. With a range, each image gets a random age.", "I giovani di FM arrivano di solito a 15–16 anni. Con un intervallo l'età è casuale per ogni immagine.", "Les jeunes de FM arrivent en général à 15–16 ans. Avec une plage, l'âge est tiré au hasard pour chaque image.", "Los juveniles de FM suelen llegar con 15–16 años. Con un rango, cada imagen recibe una edad aleatoria.", "Os jovens do FM costumam chegar com 15–16 anos. Com um intervalo, cada imagem recebe uma idade aleatória.", "FMのユース選手は通常15〜16歳で加入します。範囲を指定すると画像ごとにランダムな年齢になります。", "FM 유스 선수는 보통 15~16세에 입단합니다. 범위를 지정하면 이미지마다 나이가 무작위로 정해집니다."),
    "mix.fixed": ("Ethnie fest eingestellt – die Länder fließen trotzdem in die Beschreibung ein.", "Ethnicity is fixed – the countries are still used in the description.", "Etnia fissata – i paesi vengono comunque usati nella descrizione.", "Ethnie fixée – les pays sont tout de même utilisés dans la description.", "Etnia fija: los países se siguen usando en la descripción.", "Etnia fixa – os países continuam sendo usados na descrição.", "民族を固定中 – 国は説明文に引き続き使われます。", "민족 고정됨 – 국가는 계속 설명에 사용됩니다."),
    "mix.dist": ("Verteilung {country}: ", "Distribution {country}: ", "Distribuzione {country}: ", "Répartition {country} : ", "Distribución {country}: ", "Distribuição {country}: ", "{country}の分布：", "{country} 분포: "),
    "mix.parents": ("Eltern aus {country}: ", "Parents from {country}: ", "Genitori da {country}: ", "Parents de {country} : ", "Padres de {country}: ", "Pais de {country}: ", "{country}出身の両親：", "{country} 출신 부모: "),
    "mix.both": ("→ Aussehen wie in {second}, geboren in {country}.", "→ Looks like {second}, born in {country}.", "→ Aspetto come in {second}, nato in {country}.", "→ Apparence de {second}, né en/au {country}.", "→ Aspecto de {second}, nacido en {country}.", "→ Aparência de {second}, nascido em {country}.", "→ {second}の外見、{country}生まれ。", "→ {second}의 외모, {country} 출생."),
    "mix.one": ("→ Gemischte Herkunft aus {country} und {second}.", "→ Mixed heritage from {country} and {second}.", "→ Origine mista tra {country} e {second}.", "→ Origine mixte {country} et {second}.", "→ Origen mixto de {country} y {second}.", "→ Origem mista de {country} e {second}.", "→ {country}と{second}のミックス。", "→ {country}와 {second}의 혼혈."),
    "mix.random": ("→ Je Bild zufällig: beide Eltern oder ein Elternteil.", "→ Random per image: both parents or one parent.", "→ Casuale per immagine: entrambi i genitori o uno solo.", "→ Aléatoire par image : les deux parents ou un seul.", "→ Aleatorio por imagen: ambos padres o uno solo.", "→ Aleatório por imagem: ambos os pais ou um só.", "→ 画像ごとにランダム：両親とも／片親。", "→ 이미지마다 무작위: 부모 모두 또는 한 명."),

    # ------------------------------------------------------------------ Tab Persönlichkeit
    "pers.intro": ("Die FM-Persönlichkeit prägt Ausstrahlung und Stil des Spielers, z. B. bekommt ein Söldner eher Halstattoo, Goldkette und ein selbstgefälliges Grinsen, ein Musterprofi wirkt gepflegt und konzentriert.",
                   "The FM personality shapes the player's look and style – e.g. a Mercenary tends to get a neck tattoo, a gold chain and a smug grin, while a Model Professional looks well-groomed and focused.",
                   "La personalità di FM influenza aspetto e stile del giocatore: ad es. un Mercenario tende ad avere un tatuaggio sul collo, una catena d'oro e un sorriso compiaciuto, un Professionista modello appare curato e concentrato.",
                   "La personnalité FM influence l'allure et le style du joueur : un Mercenaire aura plutôt un tatouage au cou, une chaîne en or et un sourire suffisant, un Professionnel modèle paraît soigné et concentré.",
                   "La personalidad de FM marca el aspecto y estilo del jugador: p. ej. un Mercenario suele llevar un tatuaje en el cuello, una cadena de oro y una sonrisa engreída; un Profesional modelo se ve cuidado y concentrado.",
                   "A personalidade do FM define o visual e o estilo do jogador – ex.: um Mercenário tende a ter tatuagem no pescoço, corrente de ouro e um sorriso convencido; um Profissional modelo parece bem cuidado e concentrado.",
                   "FMの性格は選手の雰囲気やスタイルに反映されます。例：傭兵タイプは首のタトゥー、金のネックレス、得意げな笑み。模範的プロは身だしなみが整い集中した表情に。",
                   "FM 성격은 선수의 분위기와 스타일에 반영됩니다. 예: 용병형은 목 문신, 금목걸이, 거만한 미소를, 모범적인 프로는 단정하고 집중한 모습을 보입니다."),
    "lbl.personality": ("Persönlichkeit", "Personality", "Personalità", "Personnalité", "Personalidad", "Personalidade", "性格", "성격"),
    "lbl.strength": ("Ausprägung", "Intensity", "Intensità", "Intensité", "Intensidad", "Intensidade", "強さ", "강도"),
    "hint.strength": ("Dezent = 1 Merkmal, Normal = 2, Deutlich = 3. Der Gesichtsausdruck kommt von der Persönlichkeit.", "Subtle = 1 feature, Normal = 2, Strong = 3. The facial expression comes from the personality.", "Leggera = 1 caratteristica, Normale = 2, Marcata = 3. L'espressione deriva dalla personalità.", "Discrète = 1 trait, Normale = 2, Marquée = 3. L'expression du visage vient de la personnalité.", "Sutil = 1 rasgo, Normal = 2, Marcada = 3. La expresión facial viene de la personalidad.", "Sutil = 1 traço, Normal = 2, Forte = 3. A expressão facial vem da personalidade.", "控えめ＝特徴1つ、普通＝2つ、強め＝3つ。表情は性格によって決まります。", "약하게 = 특징 1개, 보통 = 2개, 강하게 = 3개. 표정은 성격에 따라 정해집니다."),
    "lbl.tattoo": ("Tattoos ab", "Tattoos from", "Tatuaggi da", "Tatouages dès", "Tatuajes desde", "Tatuagens a partir de", "タトゥー可の年齢", "문신 허용 나이"),
    "hint.tattoo": ("Mindestalter für Tattoos. Jüngere bekommen stattdessen z. B. Ohrstecker oder Kette.", "Minimum age for tattoos. Younger players get e.g. an earring or chain instead.", "Età minima per i tatuaggi. I più giovani ricevono invece ad es. un orecchino o una catenina.", "Âge minimum pour les tatouages. Les plus jeunes ont à la place p. ex. une boucle d'oreille ou une chaîne.", "Edad mínima para tatuajes. Los más jóvenes reciben en su lugar p. ej. un pendiente o una cadena.", "Idade mínima para tatuagens. Os mais novos recebem, por ex., brinco ou corrente.", "タトゥーの最低年齢。若い選手にはピアスやネックレスなどが代わりに付きます。", "문신 최소 나이. 어린 선수는 대신 귀걸이나 목걸이 등이 붙습니다."),
    "pers.list_note": ("Bei der Spielerliste wird die Spalte 'Persönlichkeit' aus dem FM-Export verwendet (falls vorhanden), sonst diese Einstellung.", "For the player list, the 'Personality' column from the FM export is used (if present), otherwise this setting.", "Per la lista giocatori si usa la colonna 'Personalità' dell'export di FM (se presente), altrimenti questa impostazione.", "Pour la liste de joueurs, la colonne « Personnalité » de l'export FM est utilisée (si présente), sinon ce réglage.", "En la lista de jugadores se usa la columna 'Personalidad' del export de FM (si existe); si no, este ajuste.", "Na lista de jogadores é usada a coluna 'Personalidade' do export do FM (se houver); caso contrário, esta configuração.", "選手リストではFMエクスポートの「性格」列があればそれを、なければこの設定を使います。", "선수 목록에서는 FM 내보내기의 '성격' 열이 있으면 그것을, 없으면 이 설정을 사용합니다."),
    "pers.expr": ("Ausdruck: {expr}\nMögliche Merkmale: {cues}", "Expression: {expr}\nPossible features: {cues}", "Espressione: {expr}\nCaratteristiche possibili: {cues}", "Expression : {expr}\nTraits possibles : {cues}", "Expresión: {expr}\nRasgos posibles: {cues}", "Expressão: {expr}\nTraços possíveis: {cues}", "表情：{expr}\n特徴の候補：{cues}", "표정: {expr}\n가능한 특징: {cues}"),
    "pers.random_hint": ("Jedes Bild bekommt eine zufällige Persönlichkeit.", "Each image gets a random personality.", "Ogni immagine riceve una personalità casuale.", "Chaque image reçoit une personnalité aléatoire.", "Cada imagen recibe una personalidad aleatoria.", "Cada imagem recebe uma personalidade aleatória.", "画像ごとにランダムな性格になります。", "이미지마다 무작위 성격이 적용됩니다."),
    "pers.none_hint": ("Optional: Die FM-Persönlichkeit prägt Ausstrahlung und Stil (z. B. Söldner: Halstattoo, Goldkette).", "Optional: the FM personality shapes look and style (e.g. Mercenary: neck tattoo, gold chain).", "Facoltativo: la personalità di FM influenza aspetto e stile (es. Mercenario: tatuaggio sul collo, catena d'oro).", "Facultatif : la personnalité FM influence l'allure et le style (p. ex. Mercenaire : tatouage au cou, chaîne en or).", "Opcional: la personalidad de FM marca aspecto y estilo (p. ej. Mercenario: tatuaje en el cuello, cadena de oro).", "Opcional: a personalidade do FM define visual e estilo (ex.: Mercenário: tatuagem no pescoço, corrente de ouro).", "任意：FMの性格が雰囲気とスタイルに反映されます（例：傭兵＝首のタトゥー、金のネックレス）。", "선택 사항: FM 성격이 분위기와 스타일에 반영됩니다 (예: 용병 = 목 문신, 금목걸이)."),

    # ------------------------------------------------------------------ Tab Aussehen
    "lbl.hair_color": ("Haarfarbe", "Hair colour", "Colore capelli", "Couleur des cheveux", "Color de pelo", "Cor do cabelo", "髪色", "머리색"),
    "lbl.hair_style": ("Frisur", "Hairstyle", "Taglio", "Coiffure", "Peinado", "Penteado", "髪型", "헤어스타일"),
    "lbl.beard": ("Bart", "Facial hair", "Barba", "Barbe", "Barba", "Barba", "ひげ", "수염"),
    "hint.beard": ("'Automatisch' wählt altersgerecht (15-Jährige meist ohne Bart).", "'Automatic' picks age-appropriately (15-year-olds mostly without facial hair).", "'Automatico' sceglie in base all'età (i 15enni di solito senza barba).", "« Automatique » choisit selon l'âge (les 15 ans le plus souvent sans barbe).", "'Automático' elige según la edad (los de 15 años casi siempre sin barba).", "'Automático' escolhe conforme a idade (aos 15 anos geralmente sem barba).", "「自動」は年齢に合わせて選びます（15歳はほぼひげなし）。", "'자동'은 나이에 맞게 선택합니다 (15세는 대부분 수염 없음)."),
    "lbl.expression": ("Ausdruck", "Expression", "Espressione", "Expression", "Expresión", "Expressão", "表情", "표정"),
    "lbl.clothing": ("Kleidung", "Clothing", "Abbigliamento", "Tenue", "Ropa", "Roupa", "服装", "복장"),
    "lbl.shirt": ("Shirt-Farbe", "Shirt colour", "Colore maglia", "Couleur du maillot", "Color de camiseta", "Cor da camisa", "シャツの色", "셔츠 색상"),
    "hint.shirt": ("z. B. in den Vereinsfarben deines Clubs.", "e.g. in your club's colours.", "ad es. nei colori del tuo club.", "p. ex. aux couleurs de ton club.", "p. ej. con los colores de tu club.", "ex.: nas cores do seu clube.", "例：クラブカラーに合わせて。", "예: 클럽 색상으로."),
    "lbl.background": ("Hintergrund", "Background", "Sfondo", "Arrière-plan", "Fondo", "Fundo", "背景", "배경"),
    "hint.background": ("'Transparent' stellt die Person per KI frei – wie bei FM-Cut-out-Facepacks.", "'Transparent' cuts out the person with AI – like FM cut-out facepacks.", "'Trasparente' scontorna la persona con l'IA, come nei facepack cut-out di FM.", "« Transparent » détoure la personne par IA, comme les facepacks cut-out de FM.", "'Transparente' recorta a la persona con IA, como los facepacks cut-out de FM.", "'Transparente' recorta a pessoa com IA, como nos facepacks cut-out do FM.", "「透明」はAIで人物を切り抜きます（FMのカットアウト顔写真パックと同様）。", "'투명'은 AI로 인물을 누끼 처리합니다 (FM 컷아웃 페이스팩과 동일)."),
    "chk.skin": ("Hautdetails (Sommersprossen, Pickel, Muttermale) für mehr Realismus", "Skin details (freckles, spots, moles) for more realism", "Dettagli della pelle (lentiggini, brufoli, nei) per più realismo", "Détails de peau (taches de rousseur, boutons, grains de beauté) pour plus de réalisme", "Detalles de piel (pecas, granos, lunares) para más realismo", "Detalhes de pele (sardas, espinhas, pintas) para mais realismo", "肌の質感（そばかす、にきび、ほくろ）でリアルさを向上", "피부 디테일 (주근깨, 여드름, 점)로 사실감 향상"),
    "lbl.extra": ("Zusatz (engl.)", "Extra (English)", "Extra (in inglese)", "Ajout (en anglais)", "Extra (en inglés)", "Extra (em inglês)", "追加（英語）", "추가 (영어)"),
    "hint.extra": ("Freitext, der an die Beschreibung angehängt wird, z. B. 'small scar on chin, green eyes'.", "Free text appended to the description, e.g. 'small scar on chin, green eyes'.", "Testo libero aggiunto alla descrizione, es. 'small scar on chin, green eyes'.", "Texte libre ajouté à la description, p. ex. « small scar on chin, green eyes ».", "Texto libre que se añade a la descripción, p. ej. 'small scar on chin, green eyes'.", "Texto livre adicionado à descrição, ex.: 'small scar on chin, green eyes'.", "説明文に追加する自由記述（英語）。例：'small scar on chin, green eyes'", "설명에 추가되는 자유 텍스트 (영어). 예: 'small scar on chin, green eyes'"),

    # ------------------------------------------------------------------ Tab Ausgabe
    "out.note": ("Der Speicherort wird unten im Fenster gewählt.", "The save location is chosen at the bottom of the window.", "La cartella di salvataggio si sceglie in basso nella finestra.", "Le dossier d'enregistrement se choisit en bas de la fenêtre.", "La carpeta de destino se elige abajo en la ventana.", "A pasta de destino é escolhida na parte de baixo da janela.", "保存先はウィンドウ下部で選択します。", "저장 위치는 창 아래쪽에서 선택합니다."),
    "chk.subfolder": ("Unterordner je Land anlegen", "Create a subfolder per country", "Crea una sottocartella per paese", "Créer un sous-dossier par pays", "Crear una subcarpeta por país", "Criar uma subpasta por país", "国ごとにサブフォルダーを作成", "국가별 하위 폴더 만들기"),
    "chk.overwrite": ("Vorhandene Dateien mit gleichem Namen überschreiben", "Overwrite existing files with the same name", "Sovrascrivi i file esistenti con lo stesso nome", "Écraser les fichiers existants du même nom", "Sobrescribir archivos existentes con el mismo nombre", "Substituir arquivos existentes com o mesmo nome", "同名の既存ファイルを上書き", "같은 이름의 기존 파일 덮어쓰기"),
    "lbl.pattern": ("Dateiname", "File name", "Nome file", "Nom de fichier", "Nombre de archivo", "Nome do arquivo", "ファイル名", "파일 이름"),
    "hint.pattern": ("Für 'Bilder generieren'. Platzhalter: {land} {herkunft} {ethnie} {alter} {geschlecht} {seed} {nr} {datum}", "For 'Generate images'. Placeholders: {land}=country {herkunft}=origin {ethnie}=ethnicity {alter}=age {geschlecht}=gender {seed} {nr}=number {datum}=date", "Per 'Genera immagini'. Segnaposto: {land}=paese {herkunft}=origine {ethnie}=etnia {alter}=età {geschlecht}=sesso {seed} {nr}=numero {datum}=data", "Pour « Générer les images ». Variables : {land}=pays {herkunft}=origine {ethnie}=ethnie {alter}=âge {geschlecht}=sexe {seed} {nr}=numéro {datum}=date", "Para 'Generar imágenes'. Marcadores: {land}=país {herkunft}=origen {ethnie}=etnia {alter}=edad {geschlecht}=sexo {seed} {nr}=número {datum}=fecha", "Para 'Gerar imagens'. Marcadores: {land}=país {herkunft}=origem {ethnie}=etnia {alter}=idade {geschlecht}=sexo {seed} {nr}=número {datum}=data", "「画像を生成」用。プレースホルダー：{land}=国 {herkunft}=出身 {ethnie}=民族 {alter}=年齢 {geschlecht}=性別 {seed} {nr}=番号 {datum}=日付", "'이미지 생성'용. 자리표시자: {land}=국가 {herkunft}=출신 {ethnie}=민족 {alter}=나이 {geschlecht}=성별 {seed} {nr}=번호 {datum}=날짜"),
    "lbl.zoom": ("Zoom", "Zoom", "Zoom", "Zoom", "Zoom", "Zoom", "ズーム", "확대"),
    "hint.zoom": ("Links = Gesicht formatfüllend, rechts = mehr Schultern sichtbar.", "Left = face fills the frame, right = more shoulders visible.", "Sinistra = volto a tutto schermo, destra = più spalle visibili.", "Gauche = visage plein cadre, droite = plus d'épaules visibles.", "Izquierda = cara a todo el encuadre, derecha = más hombros visibles.", "Esquerda = rosto preenchendo o quadro, direita = mais ombros visíveis.", "左＝顔を大きく、右＝肩まで広く。", "왼쪽 = 얼굴을 크게, 오른쪽 = 어깨까지 넓게."),
    "lbl.face_y": ("Gesichtshöhe", "Face height", "Altezza volto", "Hauteur du visage", "Altura de la cara", "Altura do rosto", "顔の高さ", "얼굴 높이"),
    "hint.face_y": ("Vertikale Position des Gesichts im Bild.", "Vertical position of the face in the image.", "Posizione verticale del volto nell'immagine.", "Position verticale du visage dans l'image.", "Posición vertical de la cara en la imagen.", "Posição vertical do rosto na imagem.", "画像内の顔の縦位置。", "이미지에서 얼굴의 세로 위치."),
    "chk.sharpen": ("Leicht nachschärfen", "Sharpen slightly", "Nitidezza leggera", "Accentuer légèrement la netteté", "Enfocar ligeramente", "Aumentar levemente a nitidez", "軽くシャープ化", "약간 선명하게"),
    "out.always": ("Ausgabe immer: 250 × 250 px, PNG", "Output always: 250 × 250 px, PNG", "Output sempre: 250 × 250 px, PNG", "Sortie toujours : 250 × 250 px, PNG", "Salida siempre: 250 × 250 px, PNG", "Saída sempre: 250 × 250 px, PNG", "出力は常に 250 × 250 px・PNG", "출력은 항상 250 × 250 px, PNG"),

    # ------------------------------------------------------------------ Tab KI
    "lbl.backend": ("Bild-KI", "Image AI", "IA immagini", "IA d'images", "IA de imágenes", "IA de imagens", "画像AI", "이미지 AI"),
    "hint.backend": ("Pollinations: online & kostenlos. Lokal: eigene Stable-Diffusion-Installation mit '--api' (offline, schnell mit guter GPU).", "Pollinations: online & free. Local: your own Stable Diffusion installation with '--api' (offline, fast with a good GPU).", "Pollinations: online e gratuita. Locale: la tua installazione di Stable Diffusion con '--api' (offline, veloce con una buona GPU).", "Pollinations : en ligne et gratuit. Local : votre propre installation de Stable Diffusion avec « --api » (hors ligne, rapide avec un bon GPU).", "Pollinations: online y gratis. Local: tu propia instalación de Stable Diffusion con '--api' (sin conexión, rápido con una buena GPU).", "Pollinations: online e grátis. Local: sua própria instalação do Stable Diffusion com '--api' (offline, rápido com uma boa GPU).", "Pollinations：オンライン・無料。ローカル：'--api'付きで起動した自分のStable Diffusion（オフライン、高性能GPUなら高速）。", "Pollinations: 온라인·무료. 로컬: '--api'로 실행한 내 Stable Diffusion (오프라인, 좋은 GPU면 빠름)."),
    "lbl.address": ("Adresse", "Address", "Indirizzo", "Adresse", "Dirección", "Endereço", "アドレス", "주소"),
    "lbl.model": ("Modell", "Model", "Modello", "Modèle", "Modelo", "Modelo", "モデル", "모델"),
    "lbl.apikey": ("API-Key (optional)", "API key (optional)", "Chiave API (facoltativa)", "Clé API (facultative)", "Clave API (opcional)", "Chave de API (opcional)", "APIキー（任意）", "API 키 (선택)"),
    "hint.apikey": ("Ohne Key: max. 1 Bild alle 45 Sekunden – das Programm wartet automatisch. Mit Key (enter.pollinations.ai) geht es ohne Wartezeit.", "Without a key: max. 1 image every 45 seconds – the program waits automatically. With a key (enter.pollinations.ai) there is no waiting.", "Senza chiave: max. 1 immagine ogni 45 secondi, il programma attende da solo. Con una chiave (enter.pollinations.ai) nessuna attesa.", "Sans clé : max. 1 image toutes les 45 secondes, le programme attend automatiquement. Avec une clé (enter.pollinations.ai), pas d'attente.", "Sin clave: máx. 1 imagen cada 45 segundos; el programa espera solo. Con clave (enter.pollinations.ai) no hay espera.", "Sem chave: no máx. 1 imagem a cada 45 segundos – o programa espera sozinho. Com chave (enter.pollinations.ai) não há espera.", "キーなし：45秒に1枚まで（自動で待機）。キーあり（enter.pollinations.ai）なら待ち時間なし。", "키 없음: 45초에 1장까지 (자동으로 대기). 키가 있으면 (enter.pollinations.ai) 대기 없음."),
    "head.local": ("Lokal (Stable Diffusion WebUI)", "Local (Stable Diffusion WebUI)", "Locale (Stable Diffusion WebUI)", "Local (Stable Diffusion WebUI)", "Local (Stable Diffusion WebUI)", "Local (Stable Diffusion WebUI)", "ローカル（Stable Diffusion WebUI）", "로컬 (Stable Diffusion WebUI)"),
    "btn.test": ("Verbindung testen", "Test connection", "Verifica connessione", "Tester la connexion", "Probar conexión", "Testar conexão", "接続テスト", "연결 테스트"),
    "btn.testing": ("Prüfe …", "Checking …", "Verifica …", "Vérification …", "Comprobando …", "Verificando …", "確認中…", "확인 중…"),
    "lbl.steps": ("Schritte", "Steps", "Passi", "Étapes", "Pasos", "Passos", "ステップ数", "스텝 수"),
    "head.general": ("Allgemein", "General", "Generale", "Général", "General", "Geral", "全般", "일반"),
    "lbl.gen_size": ("Generier-Größe", "Generation size", "Dimensione generazione", "Taille de génération", "Tamaño de generación", "Tamanho da geração", "生成サイズ", "생성 크기"),
    "hint.gen_size": ("Bild wird in dieser Größe erzeugt und dann auf 250 px verkleinert. SDXL/Flux: 1024 ideal.", "The image is generated at this size and then scaled down to 250 px. SDXL/Flux: 1024 is ideal.", "L'immagine viene generata a questa dimensione e poi ridotta a 250 px. SDXL/Flux: ideale 1024.", "L'image est générée à cette taille puis réduite à 250 px. SDXL/Flux : 1024 idéal.", "La imagen se genera a este tamaño y luego se reduce a 250 px. SDXL/Flux: 1024 es lo ideal.", "A imagem é gerada neste tamanho e depois reduzida para 250 px. SDXL/Flux: 1024 é o ideal.", "このサイズで生成し、250pxに縮小します。SDXL/Fluxは1024が最適。", "이 크기로 생성한 뒤 250px로 축소합니다. SDXL/Flux는 1024가 이상적."),
    "lbl.delay": ("Pause (Sek.)", "Pause (sec.)", "Pausa (sec.)", "Pause (s)", "Pausa (s)", "Pausa (s)", "間隔（秒）", "간격 (초)"),
    "hint.delay": ("Zusätzliche Wartezeit zwischen Bildern. Das Gratis-Limit von Pollinations hält das Programm ohnehin automatisch ein.", "Extra waiting time between images. The program respects Pollinations' free limit automatically anyway.", "Attesa aggiuntiva tra le immagini. Il limite gratuito di Pollinations viene comunque rispettato automaticamente.", "Attente supplémentaire entre les images. Le programme respecte de toute façon automatiquement la limite gratuite de Pollinations.", "Espera adicional entre imágenes. El programa respeta de todos modos el límite gratuito de Pollinations.", "Espera adicional entre imagens. O programa respeita automaticamente o limite gratuito do Pollinations.", "画像間の追加待ち時間。Pollinationsの無料制限はいずれにしても自動で守られます。", "이미지 사이의 추가 대기 시간. Pollinations 무료 제한은 어차피 자동으로 지켜집니다."),
    "status.local_set": ("Lokal eingestellt: 1024 px, keine Pause. Tipp: 'Verbindung testen' klicken.", "Set to local: 1024 px, no pause. Tip: click 'Test connection'.", "Impostato su locale: 1024 px, nessuna pausa. Suggerimento: clicca 'Verifica connessione'.", "Réglé sur local : 1024 px, pas de pause. Astuce : cliquez sur « Tester la connexion ».", "Configurado en local: 1024 px, sin pausa. Consejo: pulsa 'Probar conexión'.", "Definido como local: 1024 px, sem pausa. Dica: clique em 'Testar conexão'.", "ローカルに設定：1024px、待ち時間なし。「接続テスト」を押してください。", "로컬로 설정: 1024px, 대기 없음. '연결 테스트'를 눌러 보세요."),
    "sd.ok": ("Verbindung OK ✔\n\nAktives Modell:\n{model}", "Connection OK ✔\n\nActive model:\n{model}", "Connessione OK ✔\n\nModello attivo:\n{model}", "Connexion OK ✔\n\nModèle actif :\n{model}", "Conexión OK ✔\n\nModelo activo:\n{model}", "Conexão OK ✔\n\nModelo ativo:\n{model}", "接続OK ✔\n\n使用中のモデル：\n{model}", "연결 성공 ✔\n\n사용 중인 모델:\n{model}"),
    "sd.none": ("(keins)", "(none)", "(nessuno)", "(aucun)", "(ninguno)", "(nenhum)", "（なし）", "(없음)"),
    "sd.models": ("Verfügbare Modelle:", "Available models:", "Modelli disponibili:", "Modèles disponibles :", "Modelos disponibles:", "Modelos disponíveis:", "利用可能なモデル：", "사용 가능한 모델:"),
    "sd.fast": ("Das ist ein Schnell-Modell (Lightning/Turbo). Der Generator nutzt dafür automatisch passende Werte: 6 Schritte, CFG 1,5, Sampler DPM++ SDE Karras.", "This is a fast model (Lightning/Turbo). The generator automatically uses suitable values: 6 steps, CFG 1.5, sampler DPM++ SDE Karras.", "È un modello veloce (Lightning/Turbo). Il generatore usa automaticamente valori adatti: 6 passi, CFG 1,5, sampler DPM++ SDE Karras.", "C'est un modèle rapide (Lightning/Turbo). Le générateur utilise automatiquement des valeurs adaptées : 6 étapes, CFG 1,5, sampler DPM++ SDE Karras.", "Es un modelo rápido (Lightning/Turbo). El generador usa automáticamente valores adecuados: 6 pasos, CFG 1,5, sampler DPM++ SDE Karras.", "É um modelo rápido (Lightning/Turbo). O gerador usa automaticamente valores adequados: 6 passos, CFG 1,5, sampler DPM++ SDE Karras.", "高速モデル（Lightning/Turbo）です。自動的に最適な値を使います：6ステップ、CFG 1.5、サンプラー DPM++ SDE Karras。", "고속 모델 (Lightning/Turbo)입니다. 자동으로 알맞은 값을 사용합니다: 6스텝, CFG 1.5, 샘플러 DPM++ SDE Karras."),
    "sd.not_xl": ("Hinweis: Für beste Ergebnisse ein SDXL-Fotomodell wie 'RealVisXL' in der WebUI oben links auswählen.", "Note: for best results, select an SDXL photo model such as 'RealVisXL' at the top left of the WebUI.", "Nota: per risultati migliori scegli in alto a sinistra nella WebUI un modello fotografico SDXL come 'RealVisXL'.", "Remarque : pour de meilleurs résultats, choisissez en haut à gauche de la WebUI un modèle photo SDXL comme « RealVisXL ».", "Nota: para mejores resultados, elige arriba a la izquierda en la WebUI un modelo fotográfico SDXL como 'RealVisXL'.", "Observação: para melhores resultados, selecione no canto superior esquerdo da WebUI um modelo fotográfico SDXL como 'RealVisXL'.", "ヒント：最良の結果を得るには、WebUI左上で 'RealVisXL' などのSDXL写真モデルを選択してください。", "참고: 최상의 결과를 위해 WebUI 왼쪽 위에서 'RealVisXL' 같은 SDXL 사진 모델을 선택하세요."),

    # ------------------------------------------------------------------ Galerie
    "gal.hint": ("Erzeugte Bilder (Klick = auswählen, Doppelklick = öffnen)", "Generated images (click = select, double-click = open)", "Immagini generate (clic = seleziona, doppio clic = apri)", "Images générées (clic = sélectionner, double-clic = ouvrir)", "Imágenes generadas (clic = seleccionar, doble clic = abrir)", "Imagens geradas (clique = selecionar, duplo clique = abrir)", "生成した画像（クリック＝選択、ダブルクリック＝開く）", "생성된 이미지 (클릭 = 선택, 더블클릭 = 열기)"),
    "gal.selection": ("Auswahl (Originalgröße)", "Selection (actual size)", "Selezione (dimensione reale)", "Sélection (taille réelle)", "Selección (tamaño real)", "Seleção (tamanho real)", "選択中（実寸）", "선택 (실제 크기)"),
    "btn.reroll": ("Neu würfeln", "Re-roll", "Rigenera", "Relancer", "Regenerar", "Gerar de novo", "再生成", "다시 생성"),
    "btn.delete": ("Löschen", "Delete", "Elimina", "Supprimer", "Eliminar", "Excluir", "削除", "삭제"),
    "btn.reveal": ("Im Ordner zeigen", "Show in folder", "Mostra nella cartella", "Afficher dans le dossier", "Mostrar en carpeta", "Mostrar na pasta", "フォルダーで表示", "폴더에서 보기"),
    "btn.copy_prompt": ("Prompt kopieren", "Copy prompt", "Copia prompt", "Copier le prompt", "Copiar prompt", "Copiar prompt", "プロンプトをコピー", "프롬프트 복사"),
    "aging.title": ("Alterungs-Set:", "Ageing set:", "Set invecchiamento:", "Série vieillissement :", "Set de envejecimiento:", "Conjunto de envelhecimento:", "加齢セット：", "나이 변화 세트:"),
    "aging.with": ("ausgewähltes Gesicht mit", "selected face at", "volto selezionato a", "visage sélectionné à", "cara seleccionada con", "rosto selecionado com", "選択した顔を", "선택한 얼굴을"),
    "aging.years": ("Jahren", "years", "anni", "ans", "años", "anos", "歳で", "세로"),
    "btn.create": ("Erstellen", "Create", "Crea", "Créer", "Crear", "Criar", "作成", "만들기"),
    "sel.roots": (" (Wurzeln: {roots})", " (roots: {roots})", " (radici: {roots})", " (origines : {roots})", " (raíces: {roots})", " (raízes: {roots})", "（ルーツ：{roots}）", " (뿌리: {roots})"),
    "sel.age": ("{gender}, {age} Jahre", "{gender}, {age} years", "{gender}, {age} anni", "{gender}, {age} ans", "{gender}, {age} años", "{gender}, {age} anos", "{gender}、{age}歳", "{gender}, {age}세"),
    "sel.pers": ("Persönlichkeit: {p}", "Personality: {p}", "Personalità: {p}", "Personnalité : {p}", "Personalidad: {p}", "Personalidade: {p}", "性格：{p}", "성격: {p}"),

    # ------------------------------------------------------------------ Spielerliste
    "btn.load_list": ("Liste laden…", "Load list…", "Carica lista…", "Charger une liste…", "Cargar lista…", "Carregar lista…", "リストを読み込む…", "목록 불러오기…"),
    "btn.export_help": ("So exportierst du aus FM", "How to export from FM", "Come esportare da FM", "Comment exporter depuis FM", "Cómo exportar desde FM", "Como exportar do FM", "FMからの書き出し方", "FM에서 내보내는 방법"),
    "lbl.filename": ("Dateiname:", "File name:", "Nome file:", "Nom de fichier :", "Nombre de archivo:", "Nome do arquivo:", "ファイル名：", "파일 이름:"),
    "lbl.second_nat": ("Bei 2. Nationalität:", "With 2nd nationality:", "Con 2ª nazionalità:", "Avec 2e nationalité :", "Con 2.ª nacionalidad:", "Com 2ª nacionalidade:", "第2国籍の場合：", "이중 국적일 때:"),
    "col.name": ("Name", "Name", "Nome", "Nom", "Nombre", "Nome", "名前", "이름"),
    "col.country": ("Land", "Country", "Paese", "Pays", "País", "País", "国", "국가"),
    "col.country2": ("2. Land", "2nd country", "2° paese", "2e pays", "2.º país", "2º país", "第2の国", "두 번째 국가"),
    "col.age": ("Alter", "Age", "Età", "Âge", "Edad", "Idade", "年齢", "나이"),
    "col.status": ("Status", "Status", "Stato", "Statut", "Estado", "Status", "状態", "상태"),
    "list.change": ("Für markierte Spieler ändern:", "Change for selected players:", "Modifica per i giocatori selezionati:", "Modifier pour les joueurs sélectionnés :", "Cambiar para los jugadores seleccionados:", "Alterar para os jogadores selecionados:", "選択した選手を変更：", "선택한 선수 변경:"),
    "btn.set": ("setzen", "set", "imposta", "appliquer", "aplicar", "aplicar", "設定", "적용"),
    "btn.remove": ("Markierte entfernen", "Remove selected", "Rimuovi selezionati", "Retirer la sélection", "Quitar seleccionados", "Remover selecionados", "選択を削除", "선택 항목 제거"),
    "list.none": ("Noch keine Liste geladen.", "No list loaded yet.", "Nessuna lista caricata.", "Aucune liste chargée.", "Todavía no hay ninguna lista cargada.", "Nenhuma lista carregada ainda.", "リストはまだ読み込まれていません。", "아직 불러온 목록이 없습니다."),
    "btn.gen_all": ("▶ Für alle generieren", "▶ Generate for all", "▶ Genera per tutti", "▶ Générer pour tous", "▶ Generar para todos", "▶ Gerar para todos", "▶ 全員分を生成", "▶ 전체 생성"),
    "btn.gen_missing": ("Nur ohne Bild", "Only without image", "Solo senza immagine", "Seulement sans image", "Solo sin imagen", "Só sem imagem", "画像なしのみ", "이미지 없는 선수만"),
    "btn.gen_selected": ("Für Auswahl", "For selection", "Per la selezione", "Pour la sélection", "Para la selección", "Para a seleção", "選択した選手", "선택 항목"),
    "list.info": ("{n} Spieler · {done} mit Bild", "{n} players · {done} with image", "{n} giocatori · {done} con immagine", "{n} joueurs · {done} avec image", "{n} jugadores · {done} con imagen", "{n} jogadores · {done} com imagem", "選手 {n} 人・画像あり {done} 人", "선수 {n}명 · 이미지 있음 {done}명"),
    "list.unknown": (" · {n} mit unbekanntem Land (orange)", " · {n} with unknown country (orange)", " · {n} con paese sconosciuto (arancione)", " · {n} avec pays inconnu (orange)", " · {n} con país desconocido (naranja)", " · {n} com país desconhecido (laranja)", "・国不明 {n} 人（オレンジ）", " · 국가 미확인 {n}명 (주황색)"),
    "list.waiting": ("wartet …", "waiting …", "in attesa …", "en attente …", "en espera …", "aguardando …", "待機中…", "대기 중…"),
    "list.error": ("Fehler: {e}", "Error: {e}", "Errore: {e}", "Erreur : {e}", "Error: {e}", "Erro: {e}", "エラー：{e}", "오류: {e}"),
    "dlg.load_title": ("Spielerliste aus FM laden", "Load player list from FM", "Carica lista giocatori da FM", "Charger la liste de joueurs FM", "Cargar lista de jugadores de FM", "Carregar lista de jogadores do FM", "FMの選手リストを読み込む", "FM 선수 목록 불러오기"),
    "dlg.filetypes": ("FM-Export / Tabellen", "FM export / tables", "Export FM / tabelle", "Export FM / tableaux", "Export de FM / tablas", "Export do FM / tabelas", "FMエクスポート／表", "FM 내보내기 / 표"),
    "dlg.allfiles": ("Alle Dateien", "All files", "Tutti i file", "Tous les fichiers", "Todos los archivos", "Todos os arquivos", "すべてのファイル", "모든 파일"),
    "msg.read_error": ("Datei konnte nicht gelesen werden:\n{e}", "The file could not be read:\n{e}", "Impossibile leggere il file:\n{e}", "Impossible de lire le fichier :\n{e}", "No se pudo leer el archivo:\n{e}", "Não foi possível ler o arquivo:\n{e}", "ファイルを読み込めませんでした：\n{e}", "파일을 읽을 수 없습니다:\n{e}"),
    "msg.no_players": ("Keine Spieler gefunden.", "No players found.", "Nessun giocatore trovato.", "Aucun joueur trouvé.", "No se encontraron jugadores.", "Nenhum jogador encontrado.", "選手が見つかりません。", "선수를 찾을 수 없습니다."),
    "msg.mark_first": ("Bitte zuerst Spieler in der Liste markieren.", "Please select players in the list first.", "Seleziona prima dei giocatori nella lista.", "Sélectionnez d'abord des joueurs dans la liste.", "Primero selecciona jugadores en la lista.", "Selecione primeiro jogadores na lista.", "先にリストで選手を選択してください。", "먼저 목록에서 선수를 선택하세요."),
    "msg.load_first": ("Bitte zuerst eine Spielerliste laden (Button 'Liste laden…').", "Please load a player list first ('Load list…' button).", "Carica prima una lista giocatori (pulsante 'Carica lista…').", "Chargez d'abord une liste de joueurs (bouton « Charger une liste… »).", "Primero carga una lista de jugadores (botón 'Cargar lista…').", "Carregue primeiro uma lista de jogadores (botão 'Carregar lista…').", "先に選手リストを読み込んでください（「リストを読み込む…」ボタン）。", "먼저 선수 목록을 불러오세요 ('목록 불러오기…' 버튼)."),
    "msg.mark_players": ("Bitte Spieler in der Liste markieren (Strg/Shift + Klick).", "Please select players in the list (Ctrl/Shift + click).", "Seleziona i giocatori nella lista (Ctrl/Maiusc + clic).", "Sélectionnez des joueurs dans la liste (Ctrl/Maj + clic).", "Selecciona jugadores en la lista (Ctrl/Mayús + clic).", "Selecione jogadores na lista (Ctrl/Shift + clique).", "リストで選手を選択してください（Ctrl/Shift＋クリック）。", "목록에서 선수를 선택하세요 (Ctrl/Shift + 클릭)."),
    "status.list_gen": ("Erzeuge {n} Spielerbilder …", "Generating {n} player images …", "Generazione di {n} immagini …", "Génération de {n} images …", "Generando {n} imágenes …", "Gerando {n} imagens …", "{n} 人分の画像を生成中…", "선수 이미지 {n}개 생성 중…"),
    "help.export": (
        "So exportierst du deine Jugendspieler aus Football Manager:\n\n"
        "1. Im Spiel die Spielerliste öffnen (z. B. Kader > Jugendmannschaft oder die Jugendspieler-Vorschau).\n"
        "2. Ansicht anpassen, sodass diese Spalten sichtbar sind:\n     Name · Nat (Nationalität) · Alter\n"
        "   Optional: 2. Nationalität, Persönlichkeit und UID (Eindeutige ID).\n"
        "3. Alle Spieler markieren (Strg+A), dann Strg+P (oder Menü > 'Bildschirm drucken').\n"
        "4. 'Webseite' (.html) oder 'Textdatei' (.txt) wählen und speichern.\n"
        "5. Hier auf 'Liste laden…' klicken und die Datei auswählen.\n\n"
        "Eine eigene CSV-Datei (z. B. aus Excel) geht auch – Kopfzeile mit\nName;Nation;Alter (optional: 2. Nation;Persönlichkeit;UID).",
        "How to export your youth players from Football Manager:\n\n"
        "1. Open the player list in the game (e.g. Squad > Youth team or the youth intake preview).\n"
        "2. Adjust the view so these columns are visible:\n     Name · Nat (nationality) · Age\n"
        "   Optional: 2nd nationality, Personality and UID (unique ID).\n"
        "3. Select all players (Ctrl+A), then press Ctrl+P (or menu > 'Print screen').\n"
        "4. Choose 'Web page' (.html) or 'Text file' (.txt) and save.\n"
        "5. Click 'Load list…' here and select the file.\n\n"
        "Your own CSV file (e.g. from Excel) works too – header row with\nName;Nation;Age (optional: 2nd Nation;Personality;UID).",
        "Come esportare i tuoi giovani da Football Manager:\n\n"
        "1. Apri la lista giocatori nel gioco (es. Rosa > Giovanili o l'anteprima dei nuovi giovani).\n"
        "2. Personalizza la vista in modo che siano visibili queste colonne:\n     Nome · Naz (nazionalità) · Età\n"
        "   Facoltativo: 2ª nazionalità, Personalità e UID (ID univoco).\n"
        "3. Seleziona tutti i giocatori (Ctrl+A), poi Ctrl+P (o menu > 'Stampa schermata').\n"
        "4. Scegli 'Pagina web' (.html) o 'File di testo' (.txt) e salva.\n"
        "5. Qui clicca 'Carica lista…' e seleziona il file.\n\n"
        "Va bene anche un file CSV (es. da Excel) con intestazione\nName;Nation;Age (facoltativo: 2nd Nation;Personality;UID).",
        "Comment exporter tes jeunes depuis Football Manager :\n\n"
        "1. Ouvre la liste des joueurs dans le jeu (p. ex. Effectif > Équipe jeunes ou l'aperçu des jeunes).\n"
        "2. Personnalise la vue pour afficher ces colonnes :\n     Nom · Nat (nationalité) · Âge\n"
        "   Facultatif : 2e nationalité, Personnalité et UID (identifiant unique).\n"
        "3. Sélectionne tous les joueurs (Ctrl+A), puis Ctrl+P (ou menu > « Imprimer l'écran »).\n"
        "4. Choisis « Page web » (.html) ou « Fichier texte » (.txt) et enregistre.\n"
        "5. Ici, clique sur « Charger une liste… » et choisis le fichier.\n\n"
        "Un fichier CSV (p. ex. depuis Excel) fonctionne aussi – en-tête\nName;Nation;Age (facultatif : 2nd Nation;Personality;UID).",
        "Cómo exportar tus juveniles desde Football Manager:\n\n"
        "1. Abre la lista de jugadores en el juego (p. ej. Plantilla > Equipo juvenil o la vista previa de juveniles).\n"
        "2. Ajusta la vista para que se vean estas columnas:\n     Nombre · Nac (nacionalidad) · Edad\n"
        "   Opcional: 2.ª nacionalidad, Personalidad y UID (ID único).\n"
        "3. Selecciona todos los jugadores (Ctrl+A) y luego Ctrl+P (o menú > 'Imprimir pantalla').\n"
        "4. Elige 'Página web' (.html) o 'Archivo de texto' (.txt) y guarda.\n"
        "5. Aquí pulsa 'Cargar lista…' y elige el archivo.\n\n"
        "También sirve un CSV propio (p. ej. de Excel) con cabecera\nName;Nation;Age (opcional: 2nd Nation;Personality;UID).",
        "Como exportar seus jovens do Football Manager:\n\n"
        "1. Abra a lista de jogadores no jogo (ex.: Plantel > Equipe de base ou a prévia dos jovens).\n"
        "2. Ajuste a visualização para mostrar estas colunas:\n     Nome · Nac (nacionalidade) · Idade\n"
        "   Opcional: 2ª nacionalidade, Personalidade e UID (ID único).\n"
        "3. Selecione todos os jogadores (Ctrl+A) e pressione Ctrl+P (ou menu > 'Imprimir tela').\n"
        "4. Escolha 'Página web' (.html) ou 'Arquivo de texto' (.txt) e salve.\n"
        "5. Aqui, clique em 'Carregar lista…' e selecione o arquivo.\n\n"
        "Um CSV próprio (ex.: do Excel) também funciona – cabeçalho\nName;Nation;Age (opcional: 2nd Nation;Personality;UID).",
        "Football Managerからユース選手を書き出す方法：\n\n"
        "1. ゲーム内で選手リストを開きます（例：スカッド > ユースチーム、またはユース加入プレビュー）。\n"
        "2. 次の列が表示されるようにビューを調整します：\n     名前・国籍・年齢\n"
        "   任意：第2国籍、性格、UID（固有ID）。\n"
        "3. 全選手を選択（Ctrl+A）し、Ctrl+P（またはメニュー >「画面を印刷」）。\n"
        "4.「Webページ」(.html) または「テキストファイル」(.txt) を選んで保存します。\n"
        "5. ここで「リストを読み込む…」を押し、そのファイルを選択します。\n\n"
        "自作のCSV（Excelなど）も使えます。見出し行：\nName;Nation;Age（任意：2nd Nation;Personality;UID）",
        "Football Manager에서 유스 선수를 내보내는 방법:\n\n"
        "1. 게임에서 선수 목록을 엽니다 (예: 스쿼드 > 유스팀 또는 유스 입단 미리보기).\n"
        "2. 다음 열이 보이도록 보기를 조정합니다:\n     이름 · 국적 · 나이\n"
        "   선택: 두 번째 국적, 성격, UID (고유 ID).\n"
        "3. 모든 선수를 선택 (Ctrl+A)한 뒤 Ctrl+P (또는 메뉴 > '화면 인쇄').\n"
        "4. '웹 페이지' (.html) 또는 '텍스트 파일' (.txt)을 선택해 저장합니다.\n"
        "5. 여기서 '목록 불러오기…'를 누르고 파일을 선택합니다.\n\n"
        "직접 만든 CSV (예: Excel)도 됩니다 – 머리글:\nName;Nation;Age (선택: 2nd Nation;Personality;UID)"),

    # ------------------------------------------------------------------ untere Leiste / Meldungen
    "lbl.save_in": ("Speichern in:", "Save to:", "Salva in:", "Enregistrer dans :", "Guardar en:", "Salvar em:", "保存先：", "저장 위치:"),
    "btn.choose_dir": ("Ordner wählen…", "Choose folder…", "Scegli cartella…", "Choisir un dossier…", "Elegir carpeta…", "Escolher pasta…", "フォルダーを選択…", "폴더 선택…"),
    "btn.find_fm": ("FM-Ordner suchen", "Find FM folder", "Trova cartella FM", "Trouver le dossier FM", "Buscar carpeta de FM", "Procurar pasta do FM", "FMフォルダーを探す", "FM 폴더 찾기"),
    "btn.open": ("Öffnen", "Open", "Apri", "Ouvrir", "Abrir", "Abrir", "開く", "열기"),
    "lbl.count": ("Anzahl:", "Count:", "Quantità:", "Nombre :", "Cantidad:", "Quantidade:", "枚数：", "개수:"),
    "btn.generate": ("▶  Bilder generieren", "▶  Generate images", "▶  Genera immagini", "▶  Générer les images", "▶  Generar imágenes", "▶  Gerar imagens", "▶  画像を生成", "▶  이미지 생성"),
    "btn.cancel": ("Abbrechen", "Cancel", "Annulla", "Annuler", "Cancelar", "Cancelar", "キャンセル", "취소"),
    "status.ready": ("Bereit.", "Ready.", "Pronto.", "Prêt.", "Listo.", "Pronto.", "準備完了。", "준비 완료."),
    "dlg.choose_dir": ("Speicherort für die Bilder wählen", "Choose where to save the images", "Scegli dove salvare le immagini", "Choisir où enregistrer les images", "Elige dónde guardar las imágenes", "Escolha onde salvar as imagens", "画像の保存先を選択", "이미지 저장 위치 선택"),
    "msg.no_fm": ("Kein Football-Manager-Ordner unter 'Dokumente\\Sports Interactive' gefunden.\nBitte den Ordner selbst auswählen.", "No Football Manager folder found under 'Documents\\Sports Interactive'.\nPlease choose the folder yourself.", "Nessuna cartella di Football Manager trovata in 'Documenti\\Sports Interactive'.\nScegli la cartella manualmente.", "Aucun dossier Football Manager trouvé dans « Documents\\Sports Interactive ».\nChoisissez le dossier vous-même.", "No se encontró ninguna carpeta de Football Manager en 'Documentos\\Sports Interactive'.\nElige la carpeta manualmente.", "Nenhuma pasta do Football Manager encontrada em 'Documentos\\Sports Interactive'.\nEscolha a pasta manualmente.", "「ドキュメント\\Sports Interactive」にFootball Managerのフォルダーが見つかりません。\nフォルダーを手動で選択してください。", "'문서\\Sports Interactive'에서 Football Manager 폴더를 찾지 못했습니다.\n폴더를 직접 선택하세요."),
    "msg.fm_found": ("Gefunden:\n{fm}\n\nBilder hier speichern?\n{target}\n\nJa = diesen Ordner verwenden\nNein = selbst einen Ordner im FM-Verzeichnis auswählen", "Found:\n{fm}\n\nSave images here?\n{target}\n\nYes = use this folder\nNo = choose a folder inside the FM directory yourself", "Trovata:\n{fm}\n\nSalvare qui le immagini?\n{target}\n\nSì = usa questa cartella\nNo = scegli tu una cartella nella directory di FM", "Trouvé :\n{fm}\n\nEnregistrer les images ici ?\n{target}\n\nOui = utiliser ce dossier\nNon = choisir vous-même un dossier dans le répertoire FM", "Encontrada:\n{fm}\n\n¿Guardar las imágenes aquí?\n{target}\n\nSí = usar esta carpeta\nNo = elegir tú una carpeta dentro del directorio de FM", "Encontrada:\n{fm}\n\nSalvar as imagens aqui?\n{target}\n\nSim = usar esta pasta\nNão = escolher uma pasta dentro do diretório do FM", "見つかりました：\n{fm}\n\nここに画像を保存しますか？\n{target}\n\nはい＝このフォルダーを使用\nいいえ＝FMフォルダー内で自分で選択", "찾았습니다:\n{fm}\n\n여기에 이미지를 저장할까요?\n{target}\n\n예 = 이 폴더 사용\n아니요 = FM 폴더 안에서 직접 선택"),
    "msg.busy": ("Es läuft bereits eine Erzeugung. Bitte warten oder abbrechen.", "A generation is already running. Please wait or cancel.", "Una generazione è già in corso. Attendi o annulla.", "Une génération est déjà en cours. Patientez ou annulez.", "Ya hay una generación en curso. Espera o cancela.", "Já há uma geração em andamento. Aguarde ou cancele.", "すでに生成中です。お待ちいただくかキャンセルしてください。", "이미 생성 중입니다. 기다리거나 취소하세요."),
    "msg.dir_error": ("Speicherort kann nicht angelegt werden:\n{e}", "The save location cannot be created:\n{e}", "Impossibile creare la cartella di salvataggio:\n{e}", "Impossible de créer le dossier d'enregistrement :\n{e}", "No se puede crear la carpeta de destino:\n{e}", "Não foi possível criar a pasta de destino:\n{e}", "保存先を作成できません：\n{e}", "저장 위치를 만들 수 없습니다:\n{e}"),
    "status.generating": ("Erzeuge Bild 1 von {total} …", "Generating image 1 of {total} …", "Generazione immagine 1 di {total} …", "Génération de l'image 1 sur {total} …", "Generando imagen 1 de {total} …", "Gerando imagem 1 de {total} …", "画像 1/{total} を生成中…", "이미지 1/{total} 생성 중…"),
    "status.cancelling": ("Breche nach dem aktuellen Bild ab …", "Cancelling after the current image …", "Annullamento dopo l'immagine corrente …", "Annulation après l'image en cours …", "Cancelando tras la imagen actual …", "Cancelando após a imagem atual …", "現在の画像の後で中止します…", "현재 이미지 후 취소합니다…"),
    "status.info": ("Bild {pos} von {total}: {msg}", "Image {pos} of {total}: {msg}", "Immagine {pos} di {total}: {msg}", "Image {pos} sur {total} : {msg}", "Imagen {pos} de {total}: {msg}", "Imagem {pos} de {total}: {msg}", "画像 {pos}/{total}：{msg}", "이미지 {pos}/{total}: {msg}"),
    "status.done_one": ("{i} von {total} fertig – {name}", "{i} of {total} done – {name}", "{i} di {total} completate – {name}", "{i} sur {total} terminées – {name}", "{i} de {total} listas – {name}", "{i} de {total} prontas – {name}", "{i}/{total} 完了 – {name}", "{i}/{total} 완료 – {name}"),
    "status.error": ("Fehler bei Bild {i}: {e}", "Error in image {i}: {e}", "Errore nell'immagine {i}: {e}", "Erreur pour l'image {i} : {e}", "Error en la imagen {i}: {e}", "Erro na imagem {i}: {e}", "画像 {i} でエラー：{e}", "이미지 {i} 오류: {e}"),
    "msg.error": ("Fehler bei Bild {i}:\n\n{e}", "Error in image {i}:\n\n{e}", "Errore nell'immagine {i}:\n\n{e}", "Erreur pour l'image {i} :\n\n{e}", "Error en la imagen {i}:\n\n{e}", "Erro na imagem {i}:\n\n{e}", "画像 {i} でエラー：\n\n{e}", "이미지 {i} 오류:\n\n{e}"),
    "status.finished": ("Fertig. {n} Bild(er) gespeichert in {where}", "Done. {n} image(s) saved to {where}", "Fatto. {n} immagine/i salvata/e in {where}", "Terminé. {n} image(s) enregistrée(s) dans {where}", "Listo. {n} imagen(es) guardada(s) en {where}", "Pronto. {n} imagem(ns) salva(s) em {where}", "完了。{n} 枚を {where} に保存しました", "완료. 이미지 {n}개를 {where}에 저장했습니다"),
    "status.finished_err": (" · {n} Fehler", " · {n} error(s)", " · {n} errore/i", " · {n} erreur(s)", " · {n} error(es)", " · {n} erro(s)", "・エラー {n} 件", " · 오류 {n}개"),
    "msg.select_first": ("Bitte zuerst in der Galerie ein Bild auswählen.", "Please select an image in the gallery first.", "Seleziona prima un'immagine nella galleria.", "Sélectionnez d'abord une image dans la galerie.", "Primero selecciona una imagen en la galería.", "Selecione primeiro uma imagem na galeria.", "先にギャラリーで画像を選択してください。", "먼저 갤러리에서 이미지를 선택하세요."),
    "msg.enter_ages": ("Bitte Alter eingeben, z. B. 16, 20, 25, 30 (14–45, ohne das aktuelle Alter).", "Please enter ages, e.g. 16, 20, 25, 30 (14–45, excluding the current age).", "Inserisci le età, es. 16, 20, 25, 30 (14–45, esclusa l'età attuale).", "Saisissez des âges, p. ex. 16, 20, 25, 30 (14–45, sans l'âge actuel).", "Introduce edades, p. ej. 16, 20, 25, 30 (14–45, sin la edad actual).", "Digite idades, ex.: 16, 20, 25, 30 (14–45, sem a idade atual).", "年齢を入力してください。例：16, 20, 25, 30（14〜45、現在の年齢以外）。", "나이를 입력하세요. 예: 16, 20, 25, 30 (14~45, 현재 나이 제외)."),
    "status.aging_online": ("Hinweis: Online bleiben alle Merkmale gleich, das Gesicht ist ähnlich, aber nicht identisch.", "Note: online, all features stay the same; the face is similar but not identical.", "Nota: online tutte le caratteristiche restano uguali, il volto è simile ma non identico.", "Remarque : en ligne, tous les traits restent identiques, le visage est semblable mais pas identique.", "Nota: online todos los rasgos se mantienen; la cara es parecida, pero no idéntica.", "Observação: online todos os traços permanecem; o rosto é parecido, mas não idêntico.", "注意：オンラインでは特徴は同じですが、顔は似ているものの同一ではありません。", "참고: 온라인에서는 특징은 같지만 얼굴은 비슷할 뿐 동일하지 않습니다."),
    "status.copied": ("Prompt in die Zwischenablage kopiert.", "Prompt copied to clipboard.", "Prompt copiato negli appunti.", "Prompt copié dans le presse-papiers.", "Prompt copiado al portapapeles.", "Prompt copiado para a área de transferência.", "プロンプトをクリップボードにコピーしました。", "프롬프트를 클립보드에 복사했습니다."),

    # ------------------------------------------------------------------ Bild-KI / Freistellen / Import (andere Module)
    "be.free_wait": ("Gratis-Limit: 1 Bild alle 45 s (mit kostenlosem API-Key schneller)", "Free limit: 1 image every 45 s (faster with an API key)", "Limite gratuito: 1 immagine ogni 45 s (più veloce con una chiave API)", "Limite gratuite : 1 image toutes les 45 s (plus rapide avec une clé API)", "Límite gratuito: 1 imagen cada 45 s (más rápido con una clave API)", "Limite gratuito: 1 imagem a cada 45 s (mais rápido com chave de API)", "無料制限：45秒に1枚（APIキーで高速化）", "무료 제한: 45초에 1장 (API 키로 더 빠르게)"),
    "be.left": ("{why} – noch {s} s …", "{why} – {s} s left …", "{why} – ancora {s} s …", "{why} – encore {s} s …", "{why} – faltan {s} s …", "{why} – faltam {s} s …", "{why} – 残り {s} 秒…", "{why} – {s}초 남음…"),
    "be.generating": ("Bild wird von Pollinations erzeugt …", "Pollinations is generating the image …", "Pollinations sta generando l'immagine …", "Pollinations génère l'image …", "Pollinations está generando la imagen …", "O Pollinations está gerando a imagem …", "Pollinationsで画像を生成中…", "Pollinations에서 이미지 생성 중…"),
    "be.conn_retry": ("Verbindungsproblem, neuer Versuch", "Connection problem, retrying", "Problema di connessione, nuovo tentativo", "Problème de connexion, nouvel essai", "Problema de conexión, reintentando", "Problema de conexão, tentando novamente", "接続の問題、再試行します", "연결 문제, 다시 시도합니다"),
    "be.limit": ("Gratis-Limit von Pollinations erreicht, warte", "Pollinations free limit reached, waiting", "Limite gratuito di Pollinations raggiunto, attendo", "Limite gratuite de Pollinations atteinte, attente", "Límite gratuito de Pollinations alcanzado, esperando", "Limite gratuito do Pollinations atingido, aguardando", "Pollinationsの無料制限に達しました。待機中", "Pollinations 무료 제한 도달, 대기 중"),
    "be.busy": ("Pollinations ist ausgelastet, neuer Versuch", "Pollinations is busy, retrying", "Pollinations è sovraccarico, nuovo tentativo", "Pollinations est surchargé, nouvel essai", "Pollinations está saturado, reintentando", "O Pollinations está sobrecarregado, tentando novamente", "Pollinationsが混雑しています。再試行します", "Pollinations가 혼잡합니다. 다시 시도합니다"),
    "be.cancelled": ("Abgebrochen.", "Cancelled.", "Annullato.", "Annulé.", "Cancelado.", "Cancelado.", "中止しました。", "취소되었습니다."),
    "be.rejected": ("Pollinations hat die Anfrage abgelehnt (HTTP {code}). ", "Pollinations rejected the request (HTTP {code}). ", "Pollinations ha rifiutato la richiesta (HTTP {code}). ", "Pollinations a refusé la requête (HTTP {code}). ", "Pollinations rechazó la solicitud (HTTP {code}). ", "O Pollinations recusou a solicitação (HTTP {code}). ", "Pollinationsがリクエストを拒否しました（HTTP {code}）。", "Pollinations가 요청을 거부했습니다 (HTTP {code}). "),
    "be.check_key": ("Bitte den API-Key im Tab 'KI' prüfen. ", "Please check the API key in the 'AI' tab. ", "Controlla la chiave API nella scheda 'IA'. ", "Vérifiez la clé API dans l'onglet « IA ». ", "Revisa la clave API en la pestaña 'IA'. ", "Verifique a chave de API na aba 'IA'. ", "「AI」タブのAPIキーを確認してください。", "'AI' 탭에서 API 키를 확인하세요. "),
    "be.get_key": ("Ein kostenloser API-Key (enter.pollinations.ai) kann im Tab 'KI' eingetragen werden. ", "An API key (enter.pollinations.ai) can be entered in the 'AI' tab. ", "Una chiave API (enter.pollinations.ai) può essere inserita nella scheda 'IA'. ", "Une clé API (enter.pollinations.ai) peut être saisie dans l'onglet « IA ». ", "Se puede introducir una clave API (enter.pollinations.ai) en la pestaña 'IA'. ", "Uma chave de API (enter.pollinations.ai) pode ser inserida na aba 'IA'. ", "APIキー（enter.pollinations.ai）は「AI」タブで入力できます。", "API 키 (enter.pollinations.ai)는 'AI' 탭에서 입력할 수 있습니다. "),
    "be.answer": ("Antwort: {text}", "Response: {text}", "Risposta: {text}", "Réponse : {text}", "Respuesta: {text}", "Resposta: {text}", "応答：{text}", "응답: {text}"),
    "be.no_image": ("Pollinations hat nach mehreren Versuchen kein Bild geliefert. Letzter Fehler: {err}", "Pollinations did not deliver an image after several attempts. Last error: {err}", "Pollinations non ha fornito un'immagine dopo vari tentativi. Ultimo errore: {err}", "Pollinations n'a fourni aucune image après plusieurs essais. Dernière erreur : {err}", "Pollinations no entregó ninguna imagen tras varios intentos. Último error: {err}", "O Pollinations não entregou imagem após várias tentativas. Último erro: {err}", "Pollinationsは複数回試しても画像を返しませんでした。最後のエラー：{err}", "Pollinations가 여러 번 시도해도 이미지를 보내지 않았습니다. 마지막 오류: {err}"),
    "be.invalid_image": ("{where} hat kein gültiges Bild geliefert: {snippet}", "{where} did not return a valid image: {snippet}", "{where} non ha restituito un'immagine valida: {snippet}", "{where} n'a pas renvoyé d'image valide : {snippet}", "{where} no devolvió una imagen válida: {snippet}", "{where} não retornou uma imagem válida: {snippet}", "{where} から有効な画像が返されませんでした：{snippet}", "{where}에서 올바른 이미지를 받지 못했습니다: {snippet}"),
    "be.sd_unreachable": ("Lokale Stable-Diffusion-WebUI unter {url} nicht erreichbar. Läuft sie und wurde sie mit '--api' gestartet?", "Local Stable Diffusion WebUI at {url} is not reachable. Is it running and started with '--api'?", "La WebUI locale di Stable Diffusion su {url} non è raggiungibile. È in esecuzione e avviata con '--api'?", "La WebUI Stable Diffusion locale sur {url} est injoignable. Est-elle lancée avec « --api » ?", "No se puede acceder a la WebUI local de Stable Diffusion en {url}. ¿Está en marcha y se inició con '--api'?", "A WebUI local do Stable Diffusion em {url} não está acessível. Ela está rodando e foi iniciada com '--api'?", "{url} のローカルStable Diffusion WebUIに接続できません。'--api'付きで起動していますか？", "{url}의 로컬 Stable Diffusion WebUI에 연결할 수 없습니다. '--api'로 실행 중인가요?"),
    "be.unexpected": ("Stable Diffusion WebUI: unerwartete Antwort", "Stable Diffusion WebUI: unexpected response", "Stable Diffusion WebUI: risposta inattesa", "Stable Diffusion WebUI : réponse inattendue", "Stable Diffusion WebUI: respuesta inesperada", "Stable Diffusion WebUI: resposta inesperada", "Stable Diffusion WebUI：予期しない応答", "Stable Diffusion WebUI: 예기치 않은 응답"),
    "be.no_conn": ("Keine Verbindung zu {url}.\n\n• Läuft die Stable-Diffusion-WebUI (Forge) gerade? Das schwarze Konsolenfenster muss offen sein und 'Running on local URL' anzeigen.\n• Stimmt die Adresse? Standard ist http://127.0.0.1:7860",
                   "No connection to {url}.\n\n• Is the Stable Diffusion WebUI (Forge) running? The black console window must be open and show 'Running on local URL'.\n• Is the address correct? The default is http://127.0.0.1:7860",
                   "Nessuna connessione a {url}.\n\n• La WebUI di Stable Diffusion (Forge) è in esecuzione? La finestra nera della console deve essere aperta e mostrare 'Running on local URL'.\n• L'indirizzo è corretto? Il predefinito è http://127.0.0.1:7860",
                   "Pas de connexion à {url}.\n\n• La WebUI Stable Diffusion (Forge) est-elle lancée ? La fenêtre noire de la console doit être ouverte et afficher « Running on local URL ».\n• L'adresse est-elle correcte ? Par défaut : http://127.0.0.1:7860",
                   "Sin conexión con {url}.\n\n• ¿Está en marcha la WebUI de Stable Diffusion (Forge)? La ventana negra de la consola debe estar abierta y mostrar 'Running on local URL'.\n• ¿Es correcta la dirección? La predeterminada es http://127.0.0.1:7860",
                   "Sem conexão com {url}.\n\n• A WebUI do Stable Diffusion (Forge) está rodando? A janela preta do console precisa estar aberta e mostrar 'Running on local URL'.\n• O endereço está correto? O padrão é http://127.0.0.1:7860",
                   "{url} に接続できません。\n\n• Stable Diffusion WebUI（Forge）は起動していますか？黒いコンソール画面が開いていて 'Running on local URL' と表示されている必要があります。\n• アドレスは正しいですか？既定値は http://127.0.0.1:7860 です",
                   "{url}에 연결할 수 없습니다.\n\n• Stable Diffusion WebUI (Forge)가 실행 중인가요? 검은색 콘솔 창이 열려 있고 'Running on local URL'이 표시되어야 합니다.\n• 주소가 맞나요? 기본값은 http://127.0.0.1:7860 입니다"),
    "be.no_api": ("Die WebUI läuft, aber die Schnittstelle (API) ist aus.\n\nIn der Datei webui-user.bat die Zeile 'set COMMANDLINE_ARGS=--api' eintragen und die WebUI neu starten.",
                  "The WebUI is running, but its interface (API) is turned off.\n\nAdd the line 'set COMMANDLINE_ARGS=--api' to webui-user.bat and restart the WebUI.",
                  "La WebUI è in esecuzione ma l'interfaccia (API) è disattivata.\n\nAggiungi la riga 'set COMMANDLINE_ARGS=--api' nel file webui-user.bat e riavvia la WebUI.",
                  "La WebUI tourne, mais l'interface (API) est désactivée.\n\nAjoutez la ligne « set COMMANDLINE_ARGS=--api » dans webui-user.bat et redémarrez la WebUI.",
                  "La WebUI está en marcha, pero la interfaz (API) está desactivada.\n\nAñade la línea 'set COMMANDLINE_ARGS=--api' en webui-user.bat y reinicia la WebUI.",
                  "A WebUI está rodando, mas a interface (API) está desativada.\n\nAdicione a linha 'set COMMANDLINE_ARGS=--api' no arquivo webui-user.bat e reinicie a WebUI.",
                  "WebUIは起動していますが、インターフェース（API）が無効です。\n\nwebui-user.bat に 'set COMMANDLINE_ARGS=--api' を追加してWebUIを再起動してください。",
                  "WebUI는 실행 중이지만 인터페이스(API)가 꺼져 있습니다.\n\nwebui-user.bat에 'set COMMANDLINE_ARGS=--api' 줄을 추가하고 WebUI를 다시 시작하세요."),
    "be.webui_http": ("WebUI antwortet mit HTTP {code}: {text}", "WebUI responded with HTTP {code}: {text}", "La WebUI ha risposto con HTTP {code}: {text}", "La WebUI a répondu HTTP {code} : {text}", "La WebUI respondió con HTTP {code}: {text}", "A WebUI respondeu com HTTP {code}: {text}", "WebUIの応答：HTTP {code}：{text}", "WebUI 응답: HTTP {code}: {text}"),
    "seg.download": ("Einmaliger Download des Freistell-Modells: {pct} % ({done} von {total} MB)", "One-time download of the cut-out model: {pct} % ({done} of {total} MB)", "Download una tantum del modello di scontorno: {pct} % ({done} di {total} MB)", "Téléchargement unique du modèle de détourage : {pct} % ({done} sur {total} Mo)", "Descarga única del modelo de recorte: {pct} % ({done} de {total} MB)", "Download único do modelo de recorte: {pct} % ({done} de {total} MB)", "切り抜きモデルの初回ダウンロード：{pct}%（{done}/{total} MB）", "누끼 모델 최초 다운로드: {pct}% ({done}/{total} MB)"),
    "seg.corrupt": ("Freistell-Modell beschädigt heruntergeladen – einfache Freistellung wird verwendet.", "Cut-out model download was corrupted – using simple cut-out instead.", "Il download del modello di scontorno è danneggiato: verrà usato lo scontorno semplice.", "Le téléchargement du modèle de détourage est corrompu – détourage simple utilisé.", "La descarga del modelo de recorte está dañada; se usará el recorte simple.", "O download do modelo de recorte está corrompido – será usado o recorte simples.", "切り抜きモデルのダウンロードが破損しています。簡易切り抜きを使用します。", "누끼 모델 다운로드가 손상되었습니다. 간단한 누끼를 사용합니다."),
    "seg.failed": ("Freistell-Modell konnte nicht geladen werden ({e}) – einfache Freistellung wird verwendet.", "Cut-out model could not be downloaded ({e}) – using simple cut-out instead.", "Impossibile scaricare il modello di scontorno ({e}): verrà usato lo scontorno semplice.", "Impossible de télécharger le modèle de détourage ({e}) – détourage simple utilisé.", "No se pudo descargar el modelo de recorte ({e}); se usará el recorte simple.", "Não foi possível baixar o modelo de recorte ({e}) – será usado o recorte simples.", "切り抜きモデルを取得できませんでした（{e}）。簡易切り抜きを使用します。", "누끼 모델을 받을 수 없습니다 ({e}). 간단한 누끼를 사용합니다."),
    "pl.no_header": ("Keine Kopfzeile gefunden. Die Liste braucht mindestens die Spalten 'Name' und 'Nation' (oder 'Alter').", "No header row found. The list needs at least the columns 'Name' and 'Nation' (or 'Age').", "Nessuna intestazione trovata. La lista deve avere almeno le colonne 'Nome' e 'Nazione' (o 'Età').", "Aucune ligne d'en-tête trouvée. La liste doit contenir au moins les colonnes « Nom » et « Nation » (ou « Âge »).", "No se encontró la fila de cabecera. La lista necesita al menos las columnas 'Nombre' y 'Nación' (o 'Edad').", "Nenhum cabeçalho encontrado. A lista precisa ter pelo menos as colunas 'Nome' e 'Nação' (ou 'Idade').", "見出し行が見つかりません。少なくとも「名前」と「国籍」（または「年齢」）の列が必要です。", "머리글 행을 찾지 못했습니다. 최소한 '이름'과 '국적' (또는 '나이') 열이 필요합니다."),
    "pl.no_nat": ("Keine Spalte für die Nationalität gefunden – es wird das eingestellte Land verwendet.", "No nationality column found – the selected country will be used.", "Nessuna colonna per la nazionalità: verrà usato il paese impostato.", "Aucune colonne de nationalité trouvée – le pays choisi sera utilisé.", "No se encontró columna de nacionalidad; se usará el país elegido.", "Nenhuma coluna de nacionalidade encontrada – será usado o país escolhido.", "国籍の列が見つかりません。設定中の国を使います。", "국적 열을 찾지 못했습니다. 설정된 국가를 사용합니다."),
    "pl.no_age": ("Keine Spalte 'Alter' gefunden – es wird der eingestellte Altersbereich verwendet.", "No 'Age' column found – the selected age range will be used.", "Nessuna colonna 'Età': verrà usato l'intervallo di età impostato.", "Aucune colonne « Âge » trouvée – la plage d'âge choisie sera utilisée.", "No se encontró la columna 'Edad'; se usará el rango de edad elegido.", "Nenhuma coluna 'Idade' encontrada – será usada a faixa etária escolhida.", "「年齢」列が見つかりません。設定中の年齢範囲を使います。", "'나이' 열을 찾지 못했습니다. 설정된 나이 범위를 사용합니다."),
    "pl.unknown": ("Unbekannte Länder (die KI entscheidet hier allein anhand des Namens; du kannst sie in der Liste ändern): {names}", "Unknown countries (the AI decides from the name alone; you can change them in the list): {names}", "Paesi sconosciuti (l'IA decide solo in base al nome; puoi modificarli nella lista): {names}", "Pays inconnus (l'IA décide uniquement d'après le nom ; vous pouvez les modifier dans la liste) : {names}", "Países desconocidos (la IA decide solo por el nombre; puedes cambiarlos en la lista): {names}", "Países desconhecidos (a IA decide só pelo nome; você pode alterá-los na lista): {names}", "不明な国（AIは名前だけで判断します。リストで変更できます）：{names}", "알 수 없는 국가 (AI가 이름만으로 판단합니다. 목록에서 바꿀 수 있습니다): {names}"),
    "data.read_error": ("laender.json konnte nicht gelesen werden: {e}", "laender.json could not be read: {e}", "Impossibile leggere laender.json: {e}", "Impossible de lire laender.json : {e}", "No se pudo leer laender.json: {e}", "Não foi possível ler laender.json: {e}", "laender.json を読み込めません：{e}", "laender.json을 읽을 수 없습니다: {e}"),
    "data.bad_entry": ("laender.json: Eintrag '{name}' hat ein ungültiges Format", "laender.json: entry '{name}' has an invalid format", "laender.json: la voce '{name}' ha un formato non valido", "laender.json : l'entrée « {name} » a un format invalide", "laender.json: la entrada '{name}' tiene un formato no válido", "laender.json: a entrada '{name}' tem formato inválido", "laender.json：項目「{name}」の形式が正しくありません", "laender.json: '{name}' 항목의 형식이 잘못되었습니다"),
    "data.unknown_eth": ("laender.json: '{name}' enthält unbekannte Ethnien {keys}", "laender.json: '{name}' contains unknown ethnicities {keys}", "laender.json: '{name}' contiene etnie sconosciute {keys}", "laender.json : « {name} » contient des ethnies inconnues {keys}", "laender.json: '{name}' contiene etnias desconocidas {keys}", "laender.json: '{name}' contém etnias desconhecidas {keys}", "laender.json：「{name}」に不明な民族 {keys} があります", "laender.json: '{name}'에 알 수 없는 민족 {keys}이(가) 있습니다"),
}

# ---------------------------------------------------------------------- Auswahlwerte
# OPTIONS[Kategorie][deutscher Schlüssel] = (de, en, it, fr, es, pt, ja, ko)
OPTIONS: dict[str, dict[str, tuple[str, ...]]] = {
    "_common": {
        "Automatisch": ("Automatisch", "Automatic", "Automatico", "Automatique", "Automático", "Automático", "自動", "자동"),
        "auto_country": ("Automatisch (nach Land)", "Automatic (by country)", "Automatico (in base al paese)", "Automatique (selon le pays)", "Automático (según el país)", "Automático (pelo país)", "自動（国に応じて）", "자동 (국가 기준)"),
        "Keine": ("Keine", "None", "Nessuna", "Aucune", "Ninguna", "Nenhuma", "なし", "없음"),
        "Zufällig": ("Zufällig", "Random", "Casuale", "Aléatoire", "Aleatorio", "Aleatório", "ランダム", "무작위"),
    },
    "gender": {
        "Männlich": ("Männlich", "Male", "Maschile", "Masculin", "Masculino", "Masculino", "男性", "남성"),
        "Weiblich": ("Weiblich", "Female", "Femminile", "Féminin", "Femenino", "Feminino", "女性", "여성"),
    },
    "parent_mode": {
        "Beide Eltern aus diesem Land": ("Beide Eltern aus diesem Land", "Both parents from this country", "Entrambi i genitori da questo paese", "Les deux parents de ce pays", "Ambos padres de este país", "Ambos os pais deste país", "両親ともこの国の出身", "부모 모두 이 나라 출신"),
        "Ein Elternteil (gemischt)": ("Ein Elternteil (gemischt)", "One parent (mixed)", "Un genitore (misto)", "Un parent (mixte)", "Un progenitor (mixto)", "Um dos pais (misto)", "片親（ミックス）", "부모 중 한 명 (혼혈)"),
        "Zufällig": ("Zufällig", "Random", "Casuale", "Aléatoire", "Aleatorio", "Aleatório", "ランダム", "무작위"),
    },
    "hair_color": {
        "Schwarz": ("Schwarz", "Black", "Neri", "Noirs", "Negro", "Preto", "黒", "검정"),
        "Dunkelbraun": ("Dunkelbraun", "Dark brown", "Castano scuro", "Brun foncé", "Castaño oscuro", "Castanho-escuro", "ダークブラウン", "짙은 갈색"),
        "Braun": ("Braun", "Brown", "Castani", "Châtains", "Castaño", "Castanho", "ブラウン", "갈색"),
        "Hellbraun": ("Hellbraun", "Light brown", "Castano chiaro", "Châtain clair", "Castaño claro", "Castanho-claro", "ライトブラウン", "밝은 갈색"),
        "Blond": ("Blond", "Blond", "Biondi", "Blonds", "Rubio", "Loiro", "ブロンド", "금발"),
        "Rot": ("Rot", "Red", "Rossi", "Roux", "Pelirrojo", "Ruivo", "赤毛", "빨강"),
        "Blondiert / gefärbt": ("Blondiert / gefärbt", "Bleached / dyed", "Decolorati / tinti", "Décolorés / teints", "Decolorado / teñido", "Descolorido / tingido", "ブリーチ／染色", "탈색 / 염색"),
    },
    "hair_style": {
        "Kurz & ordentlich": ("Kurz & ordentlich", "Short & neat", "Corti e ordinati", "Courts et nets", "Corto y arreglado", "Curto e arrumado", "短く整った髪", "짧고 단정한 머리"),
        "Buzzcut": ("Buzzcut", "Buzz cut", "Rasati", "Coupe rase", "Rapado", "Raspado", "坊主", "버즈컷"),
        "Fade": ("Fade", "Fade", "Sfumatura (fade)", "Dégradé", "Degradado", "Degradê", "フェード", "페이드"),
        "Mittellang / zerzaust": ("Mittellang / zerzaust", "Medium / messy", "Medi / spettinati", "Mi-longs / décoiffés", "Media melena / despeinado", "Médio / bagunçado", "ミディアム／無造作", "중간 길이 / 헝클어진"),
        "Mittelscheitel": ("Mittelscheitel", "Middle parting", "Riga in mezzo", "Raie au milieu", "Raya al medio", "Repartido ao meio", "センター分け", "가르마 (가운데)"),
        "Locken": ("Locken", "Curls", "Ricci", "Bouclés", "Rizos", "Cachos", "カール", "곱슬머리"),
        "Afro": ("Afro", "Afro", "Afro", "Afro", "Afro", "Afro", "アフロ", "아프로"),
        "Cornrows / Braids": ("Cornrows / Braids", "Cornrows / braids", "Treccine (cornrows)", "Tresses (cornrows)", "Trenzas (cornrows)", "Tranças (cornrows)", "コーンロウ／編み込み", "콘로우 / 땋은 머리"),
        "Twists / Dreads": ("Twists / Dreads", "Twists / dreads", "Twist / dread", "Twists / dreads", "Twists / rastas", "Twists / dreads", "ツイスト／ドレッド", "트위스트 / 드레드"),
        "Lang mit Dutt": ("Lang mit Dutt", "Long with bun", "Lunghi con chignon", "Longs avec chignon", "Largo con moño", "Longo com coque", "ロング（お団子）", "긴 머리 (묶음)"),
        "Pferdeschwanz": ("Pferdeschwanz", "Ponytail", "Coda di cavallo", "Queue de cheval", "Coleta", "Rabo de cavalo", "ポニーテール", "포니테일"),
        "Dutt": ("Dutt", "Bun", "Chignon", "Chignon", "Moño", "Coque", "お団子", "올림머리"),
        "Kurz / Pixie": ("Kurz / Pixie", "Short / pixie", "Corti / pixie", "Courts / pixie", "Corto / pixie", "Curto / pixie", "ショート／ピクシー", "짧은 / 픽시컷"),
        "Schulterlang": ("Schulterlang", "Shoulder-length", "Lunghi alle spalle", "Mi-longs", "Por los hombros", "Na altura dos ombros", "肩までの長さ", "어깨 길이"),
        "Geflochten": ("Geflochten", "Braided", "Intrecciati", "Tressés", "Trenzado", "Trançado", "三つ編み", "땋은 머리"),
        "Locken zurückgebunden": ("Locken zurückgebunden", "Curls tied back", "Ricci raccolti", "Boucles attachées", "Rizos recogidos", "Cachos presos", "カールをまとめ髪", "곱슬머리 묶음"),
        "Box Braids": ("Box Braids", "Box braids", "Box braids", "Box braids", "Box braids", "Box braids", "ボックスブレイズ", "박스 브레이드"),
    },
    "facial_hair": {
        "Glattrasiert": ("Glattrasiert", "Clean-shaven", "Rasato", "Rasé de près", "Afeitado", "Barbeado", "ひげなし", "면도함"),
        "Leichter Bartschatten": ("Leichter Bartschatten", "Light shadow", "Leggera ombra di barba", "Légère ombre de barbe", "Sombra de barba ligera", "Leve sombra de barba", "うっすらひげ", "옅은 수염 자국"),
        "Dreitagebart": ("Dreitagebart", "Stubble", "Barba di tre giorni", "Barbe de trois jours", "Barba de tres días", "Barba por fazer", "無精ひげ", "3일 수염"),
        "Kurzer Vollbart": ("Kurzer Vollbart", "Short full beard", "Barba corta folta", "Barbe courte fournie", "Barba corta poblada", "Barba cheia curta", "短いフルひげ", "짧은 턱수염"),
        "Schnurrbart-Flaum": ("Schnurrbart-Flaum", "Teen moustache fuzz", "Peluria sui baffi", "Duvet de moustache", "Pelusa de bigote", "Penugem de bigode", "うぶ毛の口ひげ", "솜털 콧수염"),
    },
    "expression": {
        "Neutral (Passfoto)": ("Neutral (Passfoto)", "Neutral (passport photo)", "Neutra (fototessera)", "Neutre (photo d'identité)", "Neutra (foto de carné)", "Neutra (foto 3x4)", "無表情（証明写真）", "무표정 (증명사진)"),
        "Leichtes Lächeln": ("Leichtes Lächeln", "Slight smile", "Leggero sorriso", "Léger sourire", "Sonrisa leve", "Sorriso leve", "ほほえみ", "옅은 미소"),
        "Lächeln": ("Lächeln", "Smile", "Sorriso", "Sourire", "Sonrisa", "Sorriso", "笑顔", "미소"),
        "Gemischt (zufällig)": ("Gemischt (zufällig)", "Mixed (random)", "Misto (casuale)", "Varié (aléatoire)", "Mixto (aleatorio)", "Misto (aleatório)", "ミックス（ランダム）", "섞어서 (무작위)"),
    },
    "clothing": {
        "Schlichtes T-Shirt": ("Schlichtes T-Shirt", "Plain T-shirt", "T-shirt semplice", "T-shirt simple", "Camiseta lisa", "Camiseta lisa", "無地のTシャツ", "무지 티셔츠"),
        "Trainingsshirt": ("Trainingsshirt", "Training top", "Maglia d'allenamento", "Haut d'entraînement", "Camiseta de entrenamiento", "Camisa de treino", "トレーニングシャツ", "트레이닝 셔츠"),
        "Trikot ohne Logo": ("Trikot ohne Logo", "Jersey without logo", "Maglia senza logo", "Maillot sans logo", "Camiseta sin logo", "Camisa sem logo", "ロゴなしユニフォーム", "로고 없는 유니폼"),
        "Polo-Shirt": ("Polo-Shirt", "Polo shirt", "Polo", "Polo", "Polo", "Camisa polo", "ポロシャツ", "폴로 셔츠"),
    },
    "shirt_color": {
        "Weiß": ("Weiß", "White", "Bianco", "Blanc", "Blanco", "Branco", "白", "흰색"),
        "Schwarz": ("Schwarz", "Black", "Nero", "Noir", "Negro", "Preto", "黒", "검정"),
        "Grau": ("Grau", "Grey", "Grigio", "Gris", "Gris", "Cinza", "グレー", "회색"),
        "Dunkelblau": ("Dunkelblau", "Navy blue", "Blu scuro", "Bleu marine", "Azul marino", "Azul-marinho", "紺", "남색"),
        "Hellblau": ("Hellblau", "Light blue", "Azzurro", "Bleu ciel", "Celeste", "Azul-claro", "水色", "하늘색"),
        "Rot": ("Rot", "Red", "Rosso", "Rouge", "Rojo", "Vermelho", "赤", "빨강"),
        "Grün": ("Grün", "Green", "Verde", "Vert", "Verde", "Verde", "緑", "초록"),
        "Gelb": ("Gelb", "Yellow", "Giallo", "Jaune", "Amarillo", "Amarelo", "黄", "노랑"),
        "Orange": ("Orange", "Orange", "Arancione", "Orange", "Naranja", "Laranja", "オレンジ", "주황"),
        "Lila": ("Lila", "Purple", "Viola", "Violet", "Morado", "Roxo", "紫", "보라"),
        "Bordeaux": ("Bordeaux", "Maroon", "Granata", "Bordeaux", "Granate", "Grená", "えんじ", "버건디"),
    },
    "background": {
        "Transparent (FM-Cut-out)": ("Transparent (FM-Cut-out)", "Transparent (FM cut-out)", "Trasparente (cut-out FM)", "Transparent (cut-out FM)", "Transparente (cut-out FM)", "Transparente (cut-out FM)", "透明（FMカットアウト）", "투명 (FM 컷아웃)"),
        "Hellgrau (Studio)": ("Hellgrau (Studio)", "Light grey (studio)", "Grigio chiaro (studio)", "Gris clair (studio)", "Gris claro (estudio)", "Cinza-claro (estúdio)", "ライトグレー（スタジオ）", "밝은 회색 (스튜디오)"),
        "Weiß": ("Weiß", "White", "Bianco", "Blanc", "Blanco", "Branco", "白", "흰색"),
        "Dunkelgrau": ("Dunkelgrau", "Dark grey", "Grigio scuro", "Gris foncé", "Gris oscuro", "Cinza-escuro", "ダークグレー", "어두운 회색"),
    },
    "strength": {
        "Dezent": ("Dezent", "Subtle", "Leggera", "Discrète", "Sutil", "Sutil", "控えめ", "약하게"),
        "Normal": ("Normal", "Normal", "Normale", "Normale", "Normal", "Normal", "普通", "보통"),
        "Deutlich": ("Deutlich", "Strong", "Marcata", "Marquée", "Marcada", "Forte", "強め", "강하게"),
    },
    "list_name": {
        "Name": ("Name", "Name", "Nome", "Nom", "Nombre", "Nome", "名前", "이름"),
        "UID": ("UID", "UID", "UID", "UID", "UID", "UID", "UID", "UID"),
        "Name_UID": ("Name_UID", "Name_UID", "Nome_UID", "Nom_UID", "Nombre_UID", "Nome_UID", "名前_UID", "이름_UID"),
    },
    "backend": {
        "Pollinations (online, kostenlos)": ("Pollinations (online, kostenlos)", "Pollinations (online, free)", "Pollinations (online, gratis)", "Pollinations (en ligne, gratuit)", "Pollinations (online, gratis)", "Pollinations (online, grátis)", "Pollinations（オンライン・無料）", "Pollinations (온라인, 무료)"),
        "Lokal: Stable Diffusion WebUI (A1111/Forge)": ("Lokal: Stable Diffusion WebUI (A1111/Forge)", "Local: Stable Diffusion WebUI (A1111/Forge)", "Locale: Stable Diffusion WebUI (A1111/Forge)", "Local : Stable Diffusion WebUI (A1111/Forge)", "Local: Stable Diffusion WebUI (A1111/Forge)", "Local: Stable Diffusion WebUI (A1111/Forge)", "ローカル：Stable Diffusion WebUI（A1111/Forge）", "로컬: Stable Diffusion WebUI (A1111/Forge)"),
    },
}

# ---------------------------------------------------------------------- Ethnien: (en, it, fr, es, pt, ja, ko)
ETHNICITY_NAMES: dict[str, tuple[str, ...]] = {
    "EUR_N": ("Northern European / Scandinavian", "Nordeuropeo / scandinavo", "Nord-européen / scandinave", "Nórdico / escandinavo", "Norte-europeu / escandinavo", "北欧系", "북유럽 / 스칸디나비아계"),
    "EUR_W": ("Western / Central European", "Europeo occidentale / centrale", "Européen de l'Ouest / central", "Europeo occidental / central", "Europeu ocidental / central", "西・中央ヨーロッパ系", "서·중부 유럽계"),
    "EUR_S": ("Southern European / Mediterranean", "Sudeuropeo / mediterraneo", "Européen du Sud / méditerranéen", "Sureuropeo / mediterráneo", "Sul-europeu / mediterrâneo", "南ヨーロッパ・地中海系", "남유럽 / 지중해계"),
    "EUR_E": ("Eastern European / Slavic", "Est europeo / slavo", "Européen de l'Est / slave", "Europeo del este / eslavo", "Leste-europeu / eslavo", "東ヨーロッパ・スラブ系", "동유럽 / 슬라브계"),
    "BALKAN": ("Balkan / South-Eastern European", "Balcanico / sudest europeo", "Balkanique / Europe du Sud-Est", "Balcánico / sudeste europeo", "Balcânico / sudeste europeu", "バルカン・南東ヨーロッパ系", "발칸 / 남동유럽계"),
    "CAUCASUS": ("Caucasian (Georgia, Armenia, Azerbaijan)", "Caucasico (Georgia, Armenia, Azerbaigian)", "Caucasien (Géorgie, Arménie, Azerbaïdjan)", "Caucásico (Georgia, Armenia, Azerbaiyán)", "Caucasiano (Geórgia, Armênia, Azerbaijão)", "コーカサス系（ジョージア、アルメニア、アゼルバイジャン）", "코카서스계 (조지아, 아르메니아, 아제르바이잔)"),
    "MIDEAST": ("Middle Eastern / Turkish / Arab", "Mediorientale / turco / arabo", "Moyen-oriental / turc / arabe", "Oriente Medio / turco / árabe", "Oriente Médio / turco / árabe", "中東・トルコ・アラブ系", "중동 / 튀르키예 / 아랍계"),
    "AFR_N": ("North African / Maghreb", "Nordafricano / Maghreb", "Nord-africain / Maghreb", "Norteafricano / Magreb", "Norte-africano / Magrebe", "北アフリカ・マグレブ系", "북아프리카 / 마그레브계"),
    "AFR_W": ("West African", "Africano occidentale", "Africain de l'Ouest", "Africano occidental", "Africano ocidental", "西アフリカ系", "서아프리카계"),
    "AFR_C": ("Central / Southern African", "Africano centrale / meridionale", "Africain central / austral", "Africano central / del sur", "Africano central / austral", "中部・南部アフリカ系", "중부 / 남부 아프리카계"),
    "AFR_E": ("East African / Horn of Africa", "Africano orientale / Corno d'Africa", "Africain de l'Est / Corne de l'Afrique", "Africano oriental / Cuerno de África", "Africano oriental / Chifre da África", "東アフリカ・アフリカの角系", "동아프리카 / 아프리카의 뿔계"),
    "AFRO_DIA": ("Afro-Caribbean / African American / Afro-Latin", "Afrocaraibico / afroamericano / afrolatino", "Afro-caribéen / afro-américain / afro-latino", "Afrocaribeño / afroamericano / afrolatino", "Afro-caribenho / afro-americano / afro-latino", "アフロ・カリビアン／アフリカ系アメリカ人／アフロ・ラテン", "아프리카계 카리브 / 아프리카계 미국인 / 아프리카계 라틴"),
    "LAT": ("Latin American (Mestizo)", "Latinoamericano (meticcio)", "Latino-américain (métis)", "Latinoamericano (mestizo)", "Latino-americano (mestiço)", "ラテンアメリカ系（メスティーソ）", "라틴아메리카계 (메스티소)"),
    "INDIG": ("Indigenous (Andes / Central America)", "Indigeno (Ande / America centrale)", "Autochtone (Andes / Amérique centrale)", "Indígena (Andes / Centroamérica)", "Indígena (Andes / América Central)", "先住民系（アンデス・中米）", "원주민계 (안데스 / 중앙아메리카)"),
    "ASIA_E": ("East Asian", "Asiatico orientale", "Asiatique de l'Est", "Asiático oriental", "Asiático oriental", "東アジア系", "동아시아계"),
    "ASIA_SE": ("South-East Asian", "Sud-est asiatico", "Asiatique du Sud-Est", "Sudeste asiático", "Sudeste asiático", "東南アジア系", "동남아시아계"),
    "ASIA_S": ("South Asian (India, Pakistan, Bangladesh)", "Sud asiatico (India, Pakistan, Bangladesh)", "Sud-asiatique (Inde, Pakistan, Bangladesh)", "Surasiático (India, Pakistán, Bangladés)", "Sul-asiático (Índia, Paquistão, Bangladesh)", "南アジア系（インド、パキスタン、バングラデシュ）", "남아시아계 (인도, 파키스탄, 방글라데시)"),
    "ASIA_C": ("Central Asian", "Centroasiatico", "Asiatique central", "Centroasiático", "Centro-asiático", "中央アジア系", "중앙아시아계"),
    "PACIFIC": ("Pacific Islander / Polynesian / Māori", "Pacifico / polinesiano / maori", "Océanien / polynésien / maori", "Isleño del Pacífico / polinesio / maorí", "Ilhéu do Pacífico / polinésio / maori", "太平洋諸島・ポリネシア・マオリ系", "태평양 섬 / 폴리네시아 / 마오리계"),
    "MIXED": ("Mixed (e.g. African-European)", "Misto (es. africano-europeo)", "Métis (p. ex. africain-européen)", "Mixto (p. ej. africano-europeo)", "Misto (ex.: africano-europeu)", "ミックス（例：アフリカ系とヨーロッパ系）", "혼혈 (예: 아프리카계-유럽계)"),
}

# ---------------------------------------------------------------------- Persönlichkeiten: (it, fr, es, pt, ja, ko)
# Deutsch und Englisch sind die offiziellen FM-Namen (im Schlüssel). Die übrigen Sprachen sind
# sinngemäße Übersetzungen; angezeigt wird zusätzlich der englische FM-Name.
PERSONALITY_NAMES: dict[str, tuple[str, ...]] = {
    "Ausgewogen (Balanced)": ("Equilibrato", "Équilibré", "Equilibrado", "Equilibrado", "バランス型", "균형 잡힌"),
    "Belastbar (Resilient)": ("Resiliente", "Résilient", "Resiliente", "Resiliente", "打たれ強い", "회복력 있는"),
    "Charismatischer Führer (Charismatic Leader)": ("Leader carismatico", "Leader charismatique", "Líder carismático", "Líder carismático", "カリスマ的リーダー", "카리스마 있는 리더"),
    "Ehrgeizig (Ambitious)": ("Ambizioso", "Ambitieux", "Ambicioso", "Ambicioso", "野心的", "야심 있는"),
    "Ehrlich (Honest)": ("Onesto", "Honnête", "Honesto", "Honesto", "誠実", "정직한"),
    "Energisch (Spirited)": ("Energico", "Énergique", "Enérgico", "Enérgico", "活発", "활기찬"),
    "Erfolgshungrig (Driven)": ("Determinato al successo", "Affamé de succès", "Ambicioso de éxito", "Faminto por sucesso", "ハングリー", "성공에 굶주린"),
    "Fair (Sporting)": ("Sportivo", "Fair-play", "Deportivo", "Esportivo", "フェア", "페어플레이"),
    "Frohnatur (Jovial)": ("Gioviale", "Jovial", "Jovial", "Jovial", "陽気", "쾌활한"),
    "Führungspersönlichkeit (Leader)": ("Leader", "Leader", "Líder", "Líder", "リーダー", "리더"),
    "Geringes Selbstvertrauen (Low Self-Belief)": ("Scarsa autostima", "Manque de confiance", "Baja autoestima", "Baixa autoconfiança", "自信不足", "낮은 자신감"),
    "Hingebungsvoll (Devoted)": ("Devoto", "Dévoué", "Entregado", "Dedicado", "献身的", "헌신적인"),
    "Konsequent (Resolute)": ("Risoluto", "Résolu", "Resuelto", "Resoluto", "意志が固い", "단호한"),
    "Lässig (Casual)": ("Rilassato", "Désinvolte", "Despreocupado", "Descontraído", "気楽", "느긋한"),
    "Loyal (Loyal)": ("Leale", "Loyal", "Leal", "Leal", "忠実", "충성스러운"),
    "Modellbürger (Model Citizen)": ("Cittadino modello", "Citoyen modèle", "Ciudadano modelo", "Cidadão modelo", "模範的市民", "모범 시민"),
    "Musterprofi (Model Professional)": ("Professionista modello", "Professionnel modèle", "Profesional modelo", "Profissional modelo", "模範的プロ", "모범적인 프로"),
    "Nachlässig (Slack)": ("Svogliato", "Négligent", "Descuidado", "Desleixado", "怠惰", "게으른"),
    "Natürliche Autorität (Born Leader)": ("Leader nato", "Leader né", "Líder nato", "Líder nato", "生まれながらのリーダー", "타고난 리더"),
    "Ohne Ehrgeiz (Unambitious)": ("Senza ambizione", "Sans ambition", "Sin ambición", "Sem ambição", "野心なし", "야망 없는"),
    "Opportunist (Fickle)": ("Opportunista", "Opportuniste", "Oportunista", "Oportunista", "移り気", "변덕스러운"),
    "Perfektionist (Perfectionist)": ("Perfezionista", "Perfectionniste", "Perfeccionista", "Perfeccionista", "完璧主義者", "완벽주의자"),
    "Professionell (Professional)": ("Professionale", "Professionnel", "Profesional", "Profissional", "プロ意識が高い", "프로다운"),
    "Realist (Realist)": ("Realista", "Réaliste", "Realista", "Realista", "現実主義者", "현실주의자"),
    "Relativ ehrgeizig (Fairly Ambitious)": ("Abbastanza ambizioso", "Assez ambitieux", "Bastante ambicioso", "Razoavelmente ambicioso", "やや野心的", "꽤 야심 있는"),
    "Relativ fair (Fairly Sporting)": ("Abbastanza sportivo", "Assez fair-play", "Bastante deportivo", "Razoavelmente esportivo", "ややフェア", "꽤 페어플레이"),
    "Relativ loyal (Fairly Loyal)": ("Abbastanza leale", "Assez loyal", "Bastante leal", "Razoavelmente leal", "やや忠実", "꽤 충성스러운"),
    "Relativ professionell (Fairly Professional)": ("Abbastanza professionale", "Assez professionnel", "Bastante profesional", "Razoavelmente profissional", "ややプロ意識が高い", "꽤 프로다운"),
    "Relativ zielstrebig (Fairly Determined)": ("Abbastanza determinato", "Assez déterminé", "Bastante decidido", "Razoavelmente determinado", "やや決断力がある", "꽤 의지가 강한"),
    "Rückgratlos (Spineless)": ("Senza spina dorsale", "Sans caractère", "Sin carácter", "Sem fibra", "意気地なし", "줏대 없는"),
    "Schnell entmutigt (Easily Discouraged)": ("Facilmente scoraggiato", "Vite découragé", "Se desanima fácilmente", "Desanima facilmente", "すぐに落ち込む", "쉽게 낙담하는"),
    "Sehr ehrgeizig (Very Ambitious)": ("Molto ambizioso", "Très ambitieux", "Muy ambicioso", "Muito ambicioso", "非常に野心的", "매우 야심 있는"),
    "Sehr loyal (Very Loyal)": ("Molto leale", "Très loyal", "Muy leal", "Muito leal", "非常に忠実", "매우 충성스러운"),
    "Söldner (Mercenary)": ("Mercenario", "Mercenaire", "Mercenario", "Mercenário", "傭兵", "용병"),
    "Temperamentvoll (Temperamental)": ("Lunatico", "Caractériel", "Temperamental", "Temperamental", "気性が激しい", "다혈질"),
    "Unbeschwert (Light-Hearted)": ("Spensierato", "Insouciant", "Despreocupado y alegre", "Despreocupado", "のんき", "태평한"),
    "Unentschlossen (Low Determination)": ("Poco determinato", "Peu déterminé", "Poca determinación", "Pouca determinação", "決断力が低い", "의지가 약한"),
    "Unsportlich (Unsporting)": ("Antisportivo", "Antisportif", "Antideportivo", "Antidesportivo", "アンフェア", "비신사적인"),
    "Willensstark (Iron Willed)": ("Volontà di ferro", "Volonté de fer", "Voluntad de hierro", "Vontade de ferro", "鉄の意志", "강철 의지"),
    "Zielstrebig (Determined)": ("Determinato", "Déterminé", "Decidido", "Determinado", "決断力がある", "의지가 강한"),
}
# fmt: on
