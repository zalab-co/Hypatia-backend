import requests
from creds import yt_api_key, airtable_key, netlify_trigger_deploy_webhook
import random
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from airtable import Airtable

def run(event, context):
  
  en = {
    "yt_channels": "https://docs.google.com/spreadsheets/d/1Afa2sqOfw-pBpZLoQ357t5y4_lQQ6Fz9IFUSmZRnlMU/",
    "yt_videos_otd": "appDhlDCzW5NfMuve" # airtable
  }
  ru = {
    "yt_channels": "https://docs.google.com/spreadsheets/d/1yZDMYu927xs9R1VUXnl2auHQrBJj1xdYKWpm-8Q17AU/",
    "yt_videos_otd": "apprmUf0RylrdsQx7" # airtable
  }

  content_list = [en, ru]

  # scope = ['https://spreadsheets.google.com/feeds',
  #          'https://www.googleapis.com/auth/drive']
  scope = ["https://www.googleapis.com/auth/spreadsheets"]

  credentials = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)

  gc = gspread.authorize(credentials)

  def select_content_otd(sheet_with_yt_channels, content_otd_sheet):
    worksheet = gc.open_by_url(sheet_with_yt_channels).sheet1

    values_list = worksheet.col_values(1)

    # print(values_list)

    channels = []
    for yt_channel_url in values_list:
      channels.append(yt_channel_url[ yt_channel_url.rfind("/") + 1 : ])

    # print(channels)

    # print(yt_api_key)

    channel_data = "https://www.googleapis.com/youtube/v3/channels?part=contentDetails&id={}&key={}".format(channels[random.randrange(0, len(channels)-1)], yt_api_key)

    # print(channel_data)

    r = requests.get(channel_data)

    # print(r.status_code, r.text )

    # print( r.json() )

    r_json = r.json()

    # print(r_json)

    uploads_playlist_id = r_json["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    # print(uploads_playlist_id)

    # https://developers.google.com/apis-explorer/#p/youtube/v3/youtube.playlistItems.list?part=snippet%252CcontentDetails%252Cstatus&playlistId=UUK8sQmJBp8GCxrOtXWBpyEA&_h=1&

    get_uploads_playlist_url = "https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId={}&key={}&maxResults=50".format(uploads_playlist_id, yt_api_key)

    # print(get_uploads_playlist_url)

    channel_uploads = requests.get( get_uploads_playlist_url )

    # print(channel_uploads.status_code, channel_uploads.text)
    upload_items = channel_uploads.json()["items"]

    # print("upload_items", upload_items)

    random_nr = random.randrange(0, len(upload_items)-1)
    random_upload_item_snippet = upload_items[random_nr]["snippet"]

    random_video_id = random_upload_item_snippet["resourceId"]["videoId"]
    random_video_url = "https://youtube.com/watch?v=" + random_video_id

    channelTitle = random_upload_item_snippet["channelTitle"]

    video_title = random_upload_item_snippet["title"]
    video_description = random_upload_item_snippet["description"]

    # print(random_video_url)
    # END of fetching a random video



    # Writing to google sheets doesn't want to work. Use firebase or airtable instead.
    # Hypatia_video_otd_worksheet = gc.open("Hypatia - She'll teach you things. Daily Youtube videos.").sheet1

    # # test reading from file
    # values_list = Hypatia_video_otd_worksheet.col_values(1)
    # print(values_list)

    # # test writing
    # Hypatia_video_otd_worksheet.update_cell(1, 1, 'Bingo!')



    # Write the video of the day to firebase or airtable
    airtable = Airtable(content_otd_sheet, "Table 1", api_key=airtable_key)

    datetime_of_the_vid = datetime.datetime.today().strftime('%Y/%m/%d') 

    airtable.insert({'title': video_title + " - " + channelTitle, 'description': video_description, 'url': random_video_url, "date": datetime_of_the_vid})

  # # test
  # select_content_otd(content_list[1]["yt_channels"], content_list[1]["yt_videos_otd"])

  for x in content_list:
    select_content_otd(x["yt_channels"], x["yt_videos_otd"])

  # trigger frontend static site generation and deployment 
  requests.post(netlify_trigger_deploy_webhook)