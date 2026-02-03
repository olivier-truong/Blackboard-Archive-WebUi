from utils import *

def getWebdavUri(text: str):
    lst = text.split('a href="/bbcswebdav')[1:]
    ret = []
    for i in range(0, len(lst)):
        uriC = "/bbcswebdav" + lst[i].split('" ')[0]
        ret.append(uriC)
    return ret

def getWebAppUri(text: str):
    ret = []
    try:
        contentListPart = text.split('id="content_listContainer')[1]
        lst = contentListPart.split('a href="/webapps/blackboard/content')[1:]

        for i in range(len(lst)):
            uriW = "/webapps/blackboard/content" + lst[i].split('"')[0]
            ret.append(uriW)
    except Exception as e:
        pass
        #print("Error in getWebAppUri(...): ", e)
    return ret


def getWebdavUriR(text: str, s, buildDir: str, h: dict, base_url = "https://blackboard.esiee.fr"):
    folders = getWebAppUri(text)
    files = getWebdavUri(text)
    for i in range(len(files)):
        files[i] = (files[i], buildDir)

    for dir in folders:
        newText = s.get(base_url + dir).text
        dir_name = transformPath(newText.split("<title>")[1].split("</title>")[0].split("&ndash;")[0])
        try:
            if '<span id="pageTitleText">' in newText:
                tmpd1 = newText.split('<span id="pageTitleText">')[1].split('</span>')[0].split('style="color:#000000;">')[1]
                dir_name = transformPath(tmpd1)
        except:
            pass
        pth = os.path.join(buildDir, dir_name)
        if not(os.path.exists(pth)):
            os.mkdir(pth)
        sleep(0.5)
        files += getWebdavUriR(newText, s, pth, h, base_url = base_url)
    return files
