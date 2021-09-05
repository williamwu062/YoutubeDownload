from googleapiclient.discovery import build


class Search():
    def __init__(self, developerKey, search):
        self.youtube = build('youtube', 'v3', developerKey=developerKey)
        self.response = self.__searchResult(search)

    def __searchResult(self, search):
        request = self.youtube.search().list(
            part='snippet',
            maxResults=10,
            q=search
        )
        response = request.execute()
        return response

    def resultVideoInfo(self, i):
        videoInfo = {}

        items = self.response['items']
        videoInfo['videoId'] = items[i]['id']['videoId']
        videoInfo['title'] = items[i]['snippet']['title']
        videoInfo['description'] = items[i]['snippet']['description']
        return videoInfo