from utils import *
from ParsePage import *

__AUTHOR__      = "Glz_SQL"
__version__     = "1.4"

class Blackboard:

    def __init__(self, base: str):
        
        self.s = requests.Session()
        self.s.headers.update(BASE_HEADERS)
        self.BASE_HEADERS = BASE_HEADERS
        self.base = base
        r1 = self.s.get(f"{self.base}/")

        self.ajax_id = r1.text.split('blackboard.platform.security.NonceUtil.nonce.ajax" value="')[1].split('"')[0]

    def login(self, username: str, passwd: str):
        r2 = self.s.post(f"{self.base}/webapps/login/", headers = buildHeaders("application/x-www-form-urlencoded"), data = buildLoginForms(username, passwd, self.ajax_id))

        r3 = self.s.get(f"{self.base}/learn/api/v1/users/me?expand=systemRoles,insRoles")

        r4 = self.s.get(f"{self.base}/learn/api/v1/themes/_219_1/settings")

        _bb_id = r3.json().get("id", 'null')
        self._bb_id = _bb_id
        

    def getCourses(self):
        r5 = self.s.get(f"{self.base}/learn/api/v1/users/{self._bb_id}/memberships?expand=course.effectiveAvailability,course.permissions,courseRole&includeCount=true&limit=10000")


        CoursesJson = r5.json()

        results = CoursesJson.get("results", [])
        self._courses_dict   = {}

        for res in results:
            try:
                course = res.get("course", {})
                if course.get("isAvailable", False) and not(course.get("isClosed", True)):
                    displayName       = course.get("displayName", "No Name!")
                    displayId         = course.get("courseId", "No Id!")
                    homePageUrl       = course.get("homePageUrl", "No Url!")
                    externalAccessUrl = course.get("externalAccessUrl", "No External Url!")
                    selected = {"name": displayName, "page": self.base + homePageUrl}

                _selected_url  = selected["page"]
                _selected_name = selected["name"]
                self._courses_dict[_selected_name] = _selected_url


                
            except Exception as e:
                print(f"[Err.] ", e)
        return self._courses_dict

    def getCourseSections(self, _selected_name):
        _selected_url = self._courses_dict[_selected_name]
        try:
            r6 = self.s.get(_selected_url)
            _sections = r6.text.split('<ul id="courseMenuPalette_contents" class="courseMenu">')[1].split('</ul>')[0]
            _sections_href       = []
            _sections_title      = []
            _tmp = _sections.split('<a href="')[1:]
            for x in _tmp:
                if x.startswith('/webapps/blackboard'):
                    _sections_href.append(x.split('" ')[0])
                    y = x.split('<span title="')
                    if len(y) == 1:
                        _sections_title.append("Null")
                        continue
                    y = y[1]
                    if len(y.split('">')) > 1:
                        _sections_title.append(y.split('">')[1].split('</span>')[0])
                    else:
                        _sections_title.append("Null")
            _min_len = min(len(_sections_href), len(_sections_title))
            
            for i in range(_min_len):
                first_page = self.s.get(self.base + _sections_href[i]).text
                d1 = "./~tmp/Documents_Cours_1"
                if 'var courseTitle = "' in first_page:
                    d1 = f"./~tmp/{self.ajax_id}/" + transformPath(first_page.split('var courseTitle = "')[1].split('";')[0])
                else:
                    d1 = f"./~tmp/{self.ajax_id}/" + transformPath(first_page.split("<title>")[1].split("</title>")[0].split("&ndash;")[1])
                if not(os.path.exists(d1)):
                    os.makedirs(Path(d1))
                urls = getWebdavUriR(first_page, self.s, d1, BASE_HEADERS, base_url=self.base)
                for (url, dirs) in urls:
                    r = self.s.get(self.base + url)
                    
                    try:
                        filename = url_decode(r.headers.get("Content-Disposition").split("filename*=")[1].split("''")[1])
                    except Exception as e:
                        print("Error parsing filename:", e)
                        filename = f"{time()}." + r.headers.get("Content-Type", "raw/data").split("/")[-1]

                    sleep(0.5)
                    if r.status_code != 200:
                        print("Failed to download:", r.status_code)
                        continue
                    with open(os.path.join(dirs, filename), "wb") as f:
                        f.write(r.content)
                sleep(1)
        except IndexError as ie:
            pass
        except Exception as e:
            print("[ERR.]  ", e)

        return f"./~tmp/{self.ajax_id}/"
