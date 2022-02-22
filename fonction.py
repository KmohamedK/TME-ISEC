class ServerError(Exception):
    """
    Exception déclenchée en cas de problème côté serveur (URL incorrecte,
    accès interdit, requête mal formée, etc.)
    """
    def __init__(self, code=None, msg=None):
        self.code = code
        self.msg = msg

    def __str__(self):
        return "ERREUR {}, {}".format(self.code, self.msg)

class Connection:
    """
    Cette classe sert à ouvrir et à maintenir une connection avec le système
    UGLIX. Voir les exemples ci-dessous.

    Pour créer une instance de la classe, il faut spécifier une ``adresse de 
    base''. Les requêtes se font à partir de là, ce qui est bien pratique.
    L'adresse de base est typiquement l'adresse du système UGLIX.

    Cet objet Connection() s'utilise surtout via ses méthodes get(), post()...

    Il est conçu pour pouvoir être étendu facilement. En dériver une sous-classe
    capable de gérer des connexions chiffrées ne nécessite que 20 lignes de
    code supplémentaires.subject

    Exemple :
    >>> c = Connection()
    >>> c.get('/bin/echo')
    'usage: echo [arguments]'

    >>> print(c.get('/'))   # doctest: +ELLIPSIS
    HAL HAL HAL HAL HAL HAL HAL HAL HAL HAL HAL HAL HAL HAL HAL HAL HAL HAL HAL HAL
    ...
    """
    def __init__(self, base_url="http://isec.fil.cool/uglix"):
        self._base = base_url
        self._session = None   # au départ nous n'avons pas de cookie de session

    ############################################################################
    #                          MÉTHODES PUBLIQUES                              #
    ############################################################################
    def get(self, url):
        """
        Charge l'url demandée. Une requête HTTP GET est envoyée.

        >>> c = Connection()
        >>> c.get('/bin/echo')
        'usage: echo [arguments]'

        En cas d'erreur côté serveur, on récupère une exception.
        >>> c.get('/bin/foobar') # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        client.ServerError: ERREUR 404, ...
        """
        # prépare la requête
        request = urllib.request.Request(self._base + url, method='GET')
        return self._query(url, request)


    def post(self, url, **kwds):
        """
        Charge l'URL demandée. Une requête HTTP POST est envoyée. Il est 
        possible d'envoyer un nombre arbitraire d'arguments supplémentaires
        sous la forme de paires clef-valeur. Ces paires sont encodées sous la
        forme d'un dictionnaire JSON qui constitue le corps de la requête.

        Python permet de spécifier ces paires clef-valeurs comme des arguments
        nommés de la méthode post(). On peut envoyer des valeurs de n'importe
        quel type sérialisable en JSON.

        Par exemple, pour envoyer un paramètre nommé "string_example" de valeur
        "toto et un paramètre nommé "list_example" de valeur [True, 42, {'foo': 'bar'}],
        il faut invoquer :

        >>> c = Connection()
        >>> c.post('/bin/echo', string_example="toto", list_example=[True, 42, {'foo': 'bar'}])
        {'content_found': {'string_example': 'toto', 'list_example': [True, 42, {'foo': 'bar'}]}}

        L'idée est que la méthode post() convertit ceci en un dictionnaire JSON,
        qui ici ressemblerait à :

        {'string_example': 'toto', 'list_example': [True, 42, {'foo': 'bar'}]},

        puis l'envoie au serveur.
        """
        # prépare la requête
        request = urllib.request.Request(self._base + url, method='POST')
        data = None
        # kwds est un dictionnaire qui contient les arguments nommés. S'il
        # n'est pas vide, on l'encode en JSON et on l'ajoute au corps de la
        # requête.
        if kwds:     
            request.add_header('Content-type', 'application/json')
            data = json.dumps(kwds).encode()
        return self._query(url, request, data)


    def put(self, url, content):
        """
        Charge l'URL demandée avec une requête HTTP PUT. L'argument content
        forme le corps de la requête. Si content est de type str(), il est
        automatiquement encodé en UTF-8. cf /doc/strings pour plus de détails
        sur la question.
        """
        request = urllib.request.Request(self._base + url, method='PUT')
        if isinstance(content, str):
            content = content.encode()
        return self._query(url, request, data=content)

    ############################################################################
    #                     MÉTHODES PUBLIQUES AVANCÉES                          #
    ############################################################################


    def post_raw(self, url, data, content_type='application/octet-stream'):
        """
        Charge l'url demandée avec une requête HTTP POST. L'argument data
        forme le corps de la requête. Il doit s'agir d'un objet de type 
        bytes(). Cette méthode est d'un usage plus rare, et sert à envoyer des
        données qui n'ont pas vocation à être serialisées en JSON (comme des
        données binaires chiffrées, par exemple).

        Principalement utilisé pour étendre le client et lui ajouter des
        fonctionnalités.
        """
        request = urllib.request.Request(self._base + url, method='POST')
        request.add_header('Content-type', content_type)
        return self._query(url, request, data)

    def close_session(self):
        """
        Oublie la session actuelle. En principe, personne n'a besoin de ceci.
        """
        self._session = None


    ############################################################################
    #                          MÉTHODES INTERNES                               #
    ############################################################################

    def _pre_process(self, request):
        """
        Effectue un pré-traitement sur la requête pas encore lancée.
        Si on possède un cookie de session, on l'injecte dans les en-tête HTTP.
        """
        request.add_header('User-Agent', 'UGLIX official client v2.1 (c) sysprog')
        if self._session:
            request.add_header('Cookie', self._session)

    def _post_process(self, result, http_headers):
        """
        Effectue un post-traitement sur le résultat "brut" de la requête. En
        particulier, on décode les dictionnaires JSON, et on convertit le texte
        (encodé en UTF-8) en chaine de charactère Unicode. On peut étendre cette
        méthode pour gérer d'autres types de contenu si besoin.
        """
        if 'Content-Type' in http_headers:
            if http_headers['Content-Type'] == "application/json":
                return json.loads(result.decode())
            if http_headers['Content-Type'].startswith("text/plain"):
                return result.decode()
        # on ne sait pas ce que c'est : on laisse tel quel
        return result

    def _query(self, url, request, data=None):
        """
        Cette fonction à usage interne est appelée par get(), post(), put(),
        etc. Elle reçoit en argument une url et un objet Request() du module
        standard urllib.request.
        """
        self._pre_process(request)
        try:           
            # lance la requête. Si data n'est pas None, la requête aura un
            # corps non-vide, avec data dedans.
            with urllib.request.urlopen(request, data) as connexion:
                # récupère les en-têtes HTTP et le corps de la réponse, puis
                # ferme la connection
                headers = dict(connexion.info())
                result = connexion.read()
            
            # si on reçoit un identifiant de session, on le stocke
            if 'Set-Cookie' in headers:
                self._session = headers['Set-Cookie']

            # on effectue le post-processing, puis on renvoie les données.
            # c'est fini.
            return self._post_process(result, headers)

        except urllib.error.HTTPError as e:
            # On arrive ici si le serveur a renvoyé un code d'erreur HTTP
            # (genre 400, 403, 404, etc.). On récupère le corps de la réponse
            # car il y a peut-être des explications dedans. On a besoin des
            # en-tête pour le post-processing.
            headers = dict(e.headers)
            message = e.read()
            raise ServerError(e.code, self._post_process(message, headers)) from None

