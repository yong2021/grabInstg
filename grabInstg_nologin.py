import json
import os.path
import re
import requests
import urllib3


def getFname(display_url):
    reverse_url = display_url[::-1]
    found = re.search('gpj.*/', reverse_url)
    fn = found.group(0)
    f = fn.split('/', 1)
    fn = f[0][::-1]
    return fn


# found 10+ duplicate pic file, stop the process
duplicate_check_threshold = 21
dup_count = 0


def outputJpg(fname, imgurl):
    print(fname)
    if not os.path.isfile(fname):
        try:
            resp = requests.get(imgurl)
            with open(fname, 'wb') as jpg:
                jpg.write(resp.content)
        except Exception as exp:
            print(exp)
            return -1
    else:
        global dup_count
        dup_count = dup_count + 2
        print('found existing file, skip as dup. dupcount=' + str(dup_count))
        if dup_count > duplicate_check_threshold:
            exit(2)
        return dup_count
    return 0


userName = 'nike'
instgram = 'https://www.instagram.com/'
indexPage = instgram + userName

userFolder = r'c:\ins'
userFolder = userFolder + '\\' + userName
print(userFolder)
if not os.path.isdir(userFolder):
    os.makedirs(userFolder)
os.chdir(userFolder)

headers = {
    'User-Agent': 'Mozilla/5.0',
    'From': 'youremail@domain.com'  # This is another valid field
}

ipage = requests.get(indexPage,  headers=headers)

JSON = re.compile('window._sharedData = ({.*?});', re.DOTALL)
matches = JSON.search(ipage.content.decode('utf-8'))
jt = matches.group(1)
js = json.loads(jt)

user_id = js['entry_data']['ProfilePage'][0]['graphql']['user']['id']
user_name = js['entry_data']['ProfilePage'][0]['graphql']['user']['full_name']
user_name = user_name.replace(' ', '_')
print(user_name)
next_page_bool = js['entry_data']['ProfilePage'][0]['graphql']['user']['edge_owner_to_timeline_media']['page_info']['has_next_page']
cursor = js['entry_data']['ProfilePage'][0]['graphql']['user']['edge_owner_to_timeline_media']['page_info']['end_cursor']
print(cursor)
edges = js['entry_data']['ProfilePage'][0]['graphql']['user']['edge_owner_to_timeline_media']['edges']

count = 0
for i in edges:

    #if multiple pics in one node
    if 'edge_sidecar_to_children' in i['node'].keys():
        child_edges = i['node']['edge_sidecar_to_children']['edges']
        for j in child_edges:
            if not j['node']['is_video']:
                count = count + 1
                url = j['node']['display_url']
                of_name = getFname(url)
                outputJpg(of_name, url)
        continue

    #if just single pic
    video = i['node']['is_video']
    if not video:
        count = count + 1
        url = i['node']['display_url']

    #date_posted_timestamp = i['node']['taken_at_timestamp']
    #date_posted_human = datetime.fromtimestamp(date_posted_timestamp).strftime("%d/%m/%Y %H:%M:%S")
    #like_count = i['node']['edge_liked_by']['count'] if "edge_liked_by" in i['node'].keys() else ''
    #comment_count = i['node']['edge_media_to_comment']['count'] if 'edge_media_to_comment' in i['node'].keys() else ''
    #captions = ""
    #if i['node']['edge_media_to_caption']:
    #    for i2 in i['node']['edge_media_to_caption']['edges']:
    #        captions += i2['node']['text'] + "\n"

        of_name = getFname(url)
        outputJpg(of_name, url)

#now goto next page
while next_page_bool:
    di = {'id': user_id, 'first': 12, 'after': cursor}
    print(di)
    params = {'query_hash': 'e769aa130647d2354c40ea6a439bfc08', 'variables': json.dumps(di)}
    url = 'https://www.instagram.com/graphql/query/?' + urllib3.request.urlencode(params)
    print(url)

    rp = requests.get(url, headers=headers)

    try:
        data = rp.json()
    except Exception as exp:
        print(exp)
        print('re-try with text to json.')
        try:
            rp = requests.get(url, headers=headers)
            data = json.loads(rp.content.decode('utf-8'))
        except Exception as exp2:
            print(exp2)

    next_page_bool = data['data']['user']['edge_owner_to_timeline_media']['page_info']['has_next_page']
    cursor = data['data']['user']['edge_owner_to_timeline_media']['page_info']['end_cursor']
    edges = data['data']['user']['edge_owner_to_timeline_media']['edges']

    for i in edges:
        if 'edge_sidecar_to_children' in i['node'].keys():
            child_edges = i['node']['edge_sidecar_to_children']['edges']
            for j in child_edges:
                if not j['node']['is_video']:
                    count = count + 1
                    url = j['node']['display_url']
                    of_name = getFname(url)
                    outputJpg(of_name, url)
            continue

        video = i['node']['is_video']
        if not video:
            count = count + 1
            #url = i['node']['display_resources'][2]['src']
            url = i['node']['display_url']
            of_name = getFname(url)
            outputJpg(of_name, url)

