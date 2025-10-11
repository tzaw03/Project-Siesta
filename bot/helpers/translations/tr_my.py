class MY(object):
    __language__ = 'my'
#----------------
#
# အခြေခံ
#
#----------------
    WELCOME_MSG = "မင်္ဂလာပါ {}! Project-Siesta မှ ကြိုဆိုပါတယ်။ \n\n{}"
    DOWNLOADING = 'ဒေါင်းလုတ်ဆွဲနေသည်........'
    DOWNLOAD_PROGRESS = """
<b>╭─ တိုးတက်မှု
│
├ {0}
│
├ ပြီးစီး : <code>{1} / {2}</code>
│
├ ခေါင်းစဉ် : <code>{3}</code>
│
╰─ အမျိုးအစား : <code>{4}</code></b>
"""
    UPLOADING = 'အပ်လုတ်တင်နေသည်........'
    ZIPPING = 'ချုံ့နေသည်........'
    TASK_COMPLETED = "ဒေါင်းလုတ်ဆွဲခြင်း ပြီးစီးပါပြီ"
    
    # အသစ်: /start အတွက် Status Messages များ
    STATUS_SUBSCRIBED = "✅ **စာရင်းသွင်းအဖွဲ့ဝင်**\nသင်၏ သုံးစွဲခွင့် သက်တမ်းကုန်ဆုံးမည့်ရက်: `{expiry}`"
    STATUS_TRIAL = "⭐ **စမ်းသပ်အသုံးပြုသူ**\nကျန်ရှိသော Credit: `{credits}`. အချက်အလက်အတွက် `/trial` ကို သုံးပါ။"
    STATUS_FREE_TIER = "❌ **သုံးစွဲခွင့် မရှိပါ**\nသုံးစွဲခွင့်ရရန် သင့်ရဲ့ User ID ဖြင့် ငွေပေးချေထားသော ဖြတ်ပိုင်းကို Admin ထံ ပို့ပေးပါ။ သို့မဟုတ် ၃ ခု အခမဲ့ Credit ရယူရန် `/trial` ကို သုံးပါ။"

    # အသစ်: Trial Command Messages များ
    TRIAL_ALREADY_MEMBER = "သင့်တွင် သက်တမ်းရှိသော စာရင်းသွင်းမှု ရှိပြီးသားဖြစ်၍ Trial Credit မလိုအပ်ပါ။"
    TRIAL_ALREADY_HAVE_CREDITS = "သင့်တွင် **{credits}** Trial Credit ကျန်ရှိနေပါပြီ။ ၎င်းတို့ကို အရင်ဆုံး သုံးစွဲပါ။"
    TRIAL_COOLDOWN = "သင်သည် ပြီးခဲ့သည့် တစ်နှစ်အတွင်း Trial ကို သုံးစွဲပြီးပါပြီ။ နောက်တစ်ကြိမ် တောင်းဆိုနိုင်မည့်ရက်: **{next_date}**"
    TRIAL_GRANTED = "🎉 **Trial ခွင့်ပြုလိုက်ပါပြီ!** သင့်တွင် **{credits}** အခမဲ့ Trial Credit ရှိပါပြီ။ သင်၏ ၃ ခု အခမဲ့ ဒေါင်းလုတ်ဆွဲခွင့်ကို ပျော်ရွှင်စွာ အသုံးပြုပါ။"

    # အသစ်: Access/Download Messages များ
    ACCESS_DENIED_FULL = "❌ **သုံးစွဲခွင့် ငြင်းပယ်သည်**\nသင့်တွင် သက်တမ်းရှိသော စာရင်းသွင်းမှု သို့မဟုတ် ကျန်ရှိသော Trial Credit မရှိပါ။ သုံးစွဲခွင့်ရရန် `/start` ကို ပို့၍ အချက်အလက်များ ရယူပါ။"
    CREDIT_DEDUCTED = "💡 **Trial Credit အသုံးပြုပြီး**\nဤ ဒေါင်းလုတ်အတွက် ၁ Credit အသုံးပြုခဲ့သည်။ ကျန်ရှိသော Credit: `{credits}`."
    START_PROCESSING = "⏳ သင့် Link ကို စစ်ဆေးနေသည်..."
    
    # အသစ်: Admin Command Messages များ
    APPROVE_FORMAT = "❌ **ပုံစံမမှန်ပါ**\nအသုံးပြုပုံ: `/approve <user_id> <days>`"
    ERR_DAYS_INVALID = "ရက်အရေအတွက်သည် သုညထက် ကြီးရမည်။"
    USER_APPROVED = "✅ **အသုံးပြုသူ ခွင့်ပြုပြီး!**\nUser ID: `{user_id}`\nသက်တမ်း: `{days}` ရက်\nသက်တမ်းကုန်ဆုံး: `{expiry}`"
    
    # Generic Error
    ERROR = "မမျှော်လင့်ထားသော ပြဿနာတစ်ခု ဖြစ်ပွားခဲ့သည်: {}"
    
#----------------
#
# SETTINGS PANEL
#
#----------------
    INIT_SETTINGS_PANEL = '<b>ဘော့တ် ဆက်တင်များမှ ကြိုဆိုပါသည်</b>'
    LANGUAGE_PANEL = 'ဘော့တ်၏ ဘာသာစကားကို ရွေးချယ်ပါ'
    CORE_PANEL = 'အဓိက ဆက်တင်များကို ပြင်ဆင်ပါ'
    PROVIDERS_PANEL = 'တစ်ခုချင်းစီကို စီစဉ်သတ်မှတ်ပါ'

    TIDAL_PANEL = "Tidal ဆက်တင်များကို စီစဉ်သတ်မှတ်ပါ"
    TIDAL_AUTH_PANEL = """
Tidal အကောင့် စစ်မှန်ကြောင်း အတည်ပြုခြင်းကို စီမံပါ

<b>အကောင့် :</b> <code>{}</code>
<b>Mobile HiRes :</b> <code>{}</code>
<b>Mobile Atmos :</b> <code>{}</code>
<b>TV/Auto : </b> <code>{}</code>
"""
    TIDAL_AUTH_URL = "အောက်ပါ Link သို့သွားပြီး Login ဝင်ပါ\n{}"
    TIDAL_AUTH_SUCCESSFULL = 'Tidal တွင် Login အောင်မြင်ပါပြီ'
    TIDAL_REMOVED_SESSION = 'Tidal အတွက် Session အားလုံးကို ဖယ်ရှားပြီးပါပြီ'

    TELEGRAM_PANEL = """
<b>Telegram ဆက်တင်များ</b>

Admin များ : {2}
ခွင့်ပြုထားသော User များ : {3}
ခွင့်ပြုထားသော Chat များ : {4}
"""
    BAN_AUTH_FORMAT = '`/command {userid}` ကို သုံးပါ'
    BAN_ID = 'ဖယ်ရှားပြီး {}'
    USER_DOEST_EXIST = "ဤ ID မရှိပါ"
    USER_EXIST = 'ဤ ID ရှိပြီးသားဖြစ်သည်'
    AUTH_ID = 'ခွင့်ပြုခြင်း အောင်မြင်ပါပြီ'

#----------------
#
# BUTTONS
#
#----------------
    MAIN_MENU_BUTTON = 'ပင်မ မီနူး'
    CLOSE_BUTTON = 'ပိတ်မည်'
    PROVIDERS = 'ဝန်ဆောင်မှုများ'
    TELEGRAM = 'Telegram'
    CORE = 'Core'
    
    QOBUZ = 'Qobuz'
    DEEZER = 'Deezer'
    TIDAL = 'Tidal'

    BOT_PUBLIC = 'ဘော့တ် အများသုံး - {}'
    BOT_LANGUAGE = 'ဘာသာစကား'
    ANTI_SPAM = 'Spam ကာကွယ်ခြင်း - {}'
    LANGUAGE = 'ဘာသာစကား'
    QUALITY = 'အရည်အသွေး'
    AUTHORIZATION = "ခွင့်ပြုချက်များ"

    POST_ART_BUT = "Art Poster - {}"
    SORT_PLAYLIST = 'Playlist ကို စီရန် - {}'
    DISABLE_SORT_LINK = 'စီထားသော Link ကို ပိတ်ရန် - {}'
    PLAYLIST_CONC_BUT = "Playlist အစုလိုက် ဒေါင်းလုတ် - {}"
    PLAYLIST_ZIP = 'Playlist ကို ချုံ့ရန် - {}'
    ARTIST_BATCH_BUT = 'Artist အစုလိုက် အပ်လုတ် - {}'
    ARTIST_ZIP = 'Artist ကို ချုံ့ရန် - {}'
    ALBUM_ZIP = 'Album ကို ချုံ့ရန် - {}'

    QOBUZ_QUALITY_PANEL = '<b>Qobuz အရည်အသွေးကို ပြင်ဆင်ရန်</b>'

    TIDAL_LOGIN_TV = 'Login TV'
    TIDAL_REMOVE_LOGIN = "Login ဖယ်ရှားရန်"
    TIDAL_REFRESH_SESSION = 'Auth ကို ပြန်လည်စတင်ရန်'

    RCLONE_LINK = 'တိုက်ရိုက် Link'
    INDEX_LINK = 'Index Link'
#----------------
#
# ERRORS
#
#----------------
    ERR_NO_LINK = 'Link မတွေ့ပါ :('
    ERR_LINK_RECOGNITION = "ပေးထားသော Link ကို ခွဲခြားမသိရှိနိုင်ပါ။"
    ERR_QOBUZ_NOT_STREAMABLE = "ဤ Track/Album ကို ဒေါင်းလုတ်ဆွဲရန် မရနိုင်ပါ။"
    ERR_QOBUZ_NOT_AVAILABLE = "ဤ Track သည် သင့်ဒေသတွင် မရနိုင်ပါ။"
    ERR_LOGIN_TIDAL_TV_FAILED = "Login မအောင်မြင်ပါ : {}"
#----------------
#
# WARNINGS
#
#----------------
    WARNING_NO_TIDAL_TOKEN = 'TV/Auto token-secret မထည့်ရသေးပါ'
#----------------
#
# TRACK & ALBUM POSTS
#
#----------------
    ALBUM_TEMPLATE = """
🎶 <b>ခေါင်းစဉ် :</b> {title}
👤 <b>အနုပညာရှင် :</b> {artist}
📅 <b>ဖြန့်ချိသည့်ရက် :</b> {date}
🔢 <b>စုစုပေါင်း Track :</b> {totaltracks}
📀 <b>စုစုပေါင်း Volume :</b> {totalvolume}
💫 <b>အရည်အသွေး :</b> {quality}
📡 <b>ဝန်ဆောင်မှု :</b> {provider}
🔞 <b>အပြည့်အစုံ :</b> {explicit}
"""

    PLAYLIST_TEMPLATE = """
🎶 <b>ခေါင်းစဉ် :</b> {title}
🔢 <b>စုစုပေါင်း Track :</b> {totaltracks}
💫 <b>အရည်အသွေး :</b> {quality}
📡 <b>ဝန်ဆောင်မှု :</b> {provider}
"""

    SIMPLE_TITLE = """
အမည် : {0}
အမျိုးအစား : {1}
ဝန်ဆောင်မှု : {2}
"""

    ARTIST_TEMPLATE = """
👤 <b>အနုပညာရှင် :</b> {artist}
💫 <b>အရည်အသွေး :</b> {quality}
📡 <b>ဝန်ဆောင်မှု :</b> {provider}
"""
