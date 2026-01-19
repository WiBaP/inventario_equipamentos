from ldap3 import Server, Connection, NONE

class ADAuthService:
    def __init__(self, server_url: str = "ldap://172.21.0.145", domain: str = "LELIS"):
        self.server_url = "172.21.0.145"   
        self.domain ="LELIS"


    def authenticate(self, username: str, password: str):
        # Server CORRETO para ambientes sem SSL
        server = Server(self.server_url, get_info=NONE)

        user_dn = f"{self.domain}\\{username}"

        try:
            conn = Connection(
                server,
                user=user_dn,
                password=password,
                auto_bind=True
            )

            conn.search(
                search_base="DC=lelis,DC=com,DC=br",
                search_filter=f"(sAMAccountName={username})",
                attributes=[
                    "displayName",
                    "mail",
                    "department",
                    "manager",
                    "memberOf"
                ]
            )

            if conn.entries:
                entry = conn.entries[0]

                return {
                    "username": username,
                    "nome": entry.displayName.value,
                    "email": entry.mail.value,
                    "departamento": entry.department.value,
                    "manager": entry.manager.value,
                    "grupos": entry.memberOf.values
                }

        except Exception as e:
            print("❌ Erro ao autenticar no AD:", e)

        return None
