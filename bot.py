import os
import re
import math
import asyncio
import httpx
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ─── CONFIG ───────────────────────────────────────────────────────────────────
BOT_TOKEN   = os.environ["BOT_TOKEN"]
OWNER_ID    = int(os.environ["OWNER_ID"])
ORS_KEY     = os.environ.get("ORS_KEY", "")   # opcional mas recomendado
RAIO_FILTRO = 500    # pré-filtro em linha reta (metros)
LIMITE_ROTA = 300    # limite real de viabilidade (metros)
MAX_CTOS    = 6      # quantas CTOs consultar na ORS por verificação

# ─── BASE DE CTOs ─────────────────────────────────────────────────────────────
CTOS = [
    {"name":"CA01-R01","lat":-16.35074035889068,"lon":-48.97780308607192,"color":"vermelho"},
    {"name":"CA02-R01","lat":-16.34995707371558,"lon":-48.97772965524386,"color":"vermelho"},
    {"name":"CA03-R01","lat":-16.34958470537654,"lon":-48.97897881774206,"color":"vermelho"},
    {"name":"CA04-R01","lat":-16.35030948535314,"lon":-48.97877883439117,"color":"vermelho"},
    {"name":"CA05-R01","lat":-16.35196055321324,"lon":-48.97714144485939,"color":"vermelho"},
    {"name":"CA06-R01","lat":-16.35240160816282,"lon":-48.97634302590542,"color":"vermelho"},
    {"name":"CA07-R01","lat":-16.35314557472272,"lon":-48.97764396352418,"color":"vermelho"},
    {"name":"CA08-R01","lat":-16.35534265626467,"lon":-48.97761225057497,"color":"vermelho"},
    {"name":"CA01-R02","lat":-16.35431057056648,"lon":-48.9795303219196,"color":"vermelho"},
    {"name":"CA02-R02","lat":-16.35482409950529,"lon":-48.97851996985647,"color":"vermelho"},
    {"name":"CA03-R02","lat":-16.35559809544439,"lon":-48.98106205308895,"color":"amarelo"},
    {"name":"CA04-R02","lat":-16.35594040356371,"lon":-48.97984279229794,"color":"vermelho"},
    {"name":"CA05-R02-1/24","lat":-16.35333790827896,"lon":-48.9793665299016,"color":"vermelho"},
    {"name":"CA06-R02","lat":-16.35272012132979,"lon":-48.98009463915365,"color":"vermelho"},
    {"name":"CA07-R02","lat":-16.35287389104976,"lon":-48.98114014822256,"color":"vermelho"},
    {"name":"CA08-R02","lat":-16.35211869148456,"lon":-48.98256303908002,"color":"vermelho"},
    {"name":"CA01-R03","lat":-16.35749715244354,"lon":-48.98066400592396,"color":"vermelho"},
    {"name":"CA02-R03","lat":-16.35825483106105,"lon":-48.97942815895454,"color":"vermelho"},
    {"name":"CA03-R03","lat":-16.35655525734372,"lon":-48.98094889867805,"color":"vermelho"},
    {"name":"CA04-R03","lat":-16.35682322164433,"lon":-48.97924098989462,"color":"amarelo"},
    {"name":"CA05-R03","lat":-16.35870772894108,"lon":-48.98215716494567,"color":"vermelho"},
    {"name":"CA06-R03","lat":-16.35865781913417,"lon":-48.98042293586403,"color":"amarelo"},
    {"name":"CA07-R03","lat":-16.35942876185636,"lon":-48.98347380146352,"color":"vermelho"},
    {"name":"CA08-R03","lat":-16.35618379915008,"lon":-48.98277146867083,"color":"vermelho"},
    {"name":"CA01-R04","lat":-16.35491270864675,"lon":-48.98387559627827,"color":"vermelho"},
    {"name":"CA02-R04-1/16","lat":-16.35484858315424,"lon":-48.98250417033211,"color":"vermelho"},
    {"name":"CA03-R04","lat":-16.35423811312089,"lon":-48.98369324403669,"color":"vermelho"},
    {"name":"CA04-R04","lat":-16.356459661883,"lon":-48.98440140963204,"color":"vermelho"},
    {"name":"CA05-R04","lat":-16.35855683922373,"lon":-48.98604838572862,"color":"vermelho"},
    {"name":"CA06-R04","lat":-16.35699114578243,"lon":-48.98554183865607,"color":"vermelho"},
    {"name":"CA07-R04","lat":-16.35587255280514,"lon":-48.98608966203563,"color":"vermelho"},
    {"name":"CA08-R04","lat":-16.35731103917822,"lon":-48.98694288792545,"color":"amarelo"},
    {"name":"CA01-R05","lat":-16.35998008258692,"lon":-48.98477130509023,"color":"vermelho"},
    {"name":"CA02-R05","lat":-16.35802757048882,"lon":-48.98413206758651,"color":"vermelho"},
    {"name":"CA03-R05","lat":-16.36227799267283,"lon":-48.98623992592349,"color":"vermelho"},
    {"name":"CA04-R05","lat":-16.35998436343308,"lon":-48.98623082572449,"color":"amarelo"},
    {"name":"CA05-R05","lat":-16.36012976094703,"lon":-48.98718657137631,"color":"vermelho"},
    {"name":"CA06-R05","lat":-16.36099858171907,"lon":-48.98694489998151,"color":"vermelho"},
    {"name":"CA07-R05","lat":-16.36099402100547,"lon":-48.98811554769548,"color":"vermelho"},
    {"name":"CA08-R05-1/16","lat":-16.36210803471364,"lon":-48.98763677626544,"color":"vermelho"},
    {"name":"CA01-R06","lat":-16.3607855129512,"lon":-48.98420833617541,"color":"vermelho"},
    {"name":"CA02-R06-1/16","lat":-16.36123033391713,"lon":-48.98470039410749,"color":"vermelho"},
    {"name":"CA03-R06","lat":-16.3623369160123,"lon":-48.98442913574486,"color":"amarelo"},
    {"name":"CA04-R06","lat":-16.36326998260151,"lon":-48.98432187148674,"color":"amarelo"},
    {"name":"CA05-R06","lat":-16.36328414234578,"lon":-48.98359959481179,"color":"amarelo"},
    {"name":"CA06-R06","lat":-16.36007402952916,"lon":-48.98267574174729,"color":"amarelo"},
    {"name":"CA07-R06","lat":-16.3607360354816,"lon":-48.981888294807,"color":"vermelho"},
    {"name":"CA08-R06","lat":-16.36096965887324,"lon":-48.98161114979557,"color":"amarelo"},
    {"name":"CA01-R07","lat":-16.36387263721429,"lon":-48.98741106548801,"color":"vermelho"},
    {"name":"CA02-R07","lat":-16.36266447109874,"lon":-48.98799008361192,"color":"vermelho"},
    {"name":"CA03-R07","lat":-16.36475473769672,"lon":-48.98837079880624,"color":"amarelo"},
    {"name":"CA04-R07","lat":-16.36379776321635,"lon":-48.98870282779709,"color":"vermelho"},
    {"name":"CA05-R07-1/16","lat":-16.36611738552746,"lon":-48.98921505671892,"color":"vermelho"},
    {"name":"CA06-R07","lat":-16.3649228158091,"lon":-48.98625724779216,"color":"amarelo"},
    {"name":"CA07-R07","lat":-16.36519321675426,"lon":-48.98536334816234,"color":"vermelho"},
    {"name":"CA08-R07","lat":-16.36392844477424,"lon":-48.98585249625722,"color":"vermelho"},
    {"name":"CA01-R08","lat":-16.37068413374145,"lon":-48.98919736662501,"color":"amarelo"},
    {"name":"CA02-R08","lat":-16.37099785346702,"lon":-48.98873541372103,"color":"vermelho"},
    {"name":"CA03-R08","lat":-16.36875223186384,"lon":-48.98970190188537,"color":"vermelho"},
    {"name":"CA04-R08","lat":-16.36863118924703,"lon":-48.9903004707861,"color":"amarelo"},
    {"name":"CA05-R08","lat":-16.36813593461477,"lon":-48.98856234268871,"color":"amarelo"},
    {"name":"CA06-R08","lat":-16.36570149707665,"lon":-48.98831951375576,"color":"vermelho"},
    {"name":"CA07-R08","lat":-16.36707281419849,"lon":-48.98789027244651,"color":"vermelho"},
    {"name":"CA08-R08","lat":-16.36711998495656,"lon":-48.98689460006854,"color":"vermelho"},
    {"name":"CA01-R09","lat":-16.37194977149165,"lon":-48.98802729550354,"color":"vermelho"},
    {"name":"CA02-R09","lat":-16.37290756752751,"lon":-48.98868839398522,"color":"vermelho"},
    {"name":"CA03-R09","lat":-16.37190836456388,"lon":-48.98762410295286,"color":"amarelo"},
    {"name":"CA04-R09","lat":-16.37281250841596,"lon":-48.9878281784001,"color":"amarelo"},
    {"name":"CA05-R09","lat":-16.37017620393586,"lon":-48.98723178323544,"color":"verde"},
    {"name":"CA06-R09","lat":-16.36916501808205,"lon":-48.98798183771113,"color":"amarelo"},
    {"name":"CA07-R09-1/24","lat":-16.3691850351939,"lon":-48.98653385835686,"color":"vermelho"},
    {"name":"CA08-R09-1/16","lat":-16.36936340978815,"lon":-48.98580661258637,"color":"vermelho"},
    {"name":"CA01-R10","lat":-16.36957463753852,"lon":-48.98504240378301,"color":"amarelo"},
    {"name":"CA02-R10-1/16","lat":-16.36943007284341,"lon":-48.98536831001508,"color":"vermelho"},
    {"name":"CA03-R10","lat":-16.36574009912246,"lon":-48.98412043590042,"color":"vermelho"},
    {"name":"CA04-R10","lat":-16.37173673123715,"lon":-48.98554250749201,"color":"vermelho"},
    {"name":"CA05-R10","lat":-16.37276601872599,"lon":-48.98606114882376,"color":"vermelho"},
    {"name":"CA06-R10","lat":-16.37370326743891,"lon":-48.98643789376222,"color":"vermelho"},
    {"name":"CA07-R10","lat":-16.37506463671186,"lon":-48.98446430834336,"color":"vermelho"},
    {"name":"CA08-R10","lat":-16.37434938710119,"lon":-48.9871087149835,"color":"amarelo"},
    {"name":"CA01-R11","lat":-16.3747269825584,"lon":-48.98829757293301,"color":"vermelho"},
    {"name":"CA02-R11","lat":-16.37451451236164,"lon":-48.98917692572896,"color":"vermelho"},
    {"name":"CA03-R11","lat":-16.37504072521397,"lon":-48.98799073169512,"color":"vermelho"},
    {"name":"CA04-R11","lat":-16.37599198631902,"lon":-48.98899995427968,"color":"amarelo"},
    {"name":"CA05-R11","lat":-16.37605378762421,"lon":-48.98544532569069,"color":"vermelho"},
    {"name":"CA06-R11","lat":-16.37721307126212,"lon":-48.98662415145626,"color":"vermelho"},
    {"name":"CA07-R11","lat":-16.37639670603694,"lon":-48.98791346548529,"color":"vermelho"},
    {"name":"CA08-R11","lat":-16.37810795241795,"lon":-48.98753590083352,"color":"amarelo"},
    {"name":"CA01-R12","lat":-16.3766581023358,"lon":-48.98550368780104,"color":"amarelo"},
    {"name":"CA02-R12-1/16","lat":-16.37597284880256,"lon":-48.9848134367068,"color":"vermelho"},
    {"name":"CA03-R12","lat":-16.37739759407445,"lon":-48.98274711708367,"color":"vermelho"},
    {"name":"CA04-R12","lat":-16.37786448517305,"lon":-48.98362711401507,"color":"vermelho"},
    {"name":"CA05-R12","lat":-16.37731483699339,"lon":-48.98615167577162,"color":"vermelho"},
    {"name":"CA06-R12","lat":-16.37804091684858,"lon":-48.98689327955792,"color":"vermelho"},
    {"name":"CA07-R12","lat":-16.37870574591107,"lon":-48.98753786154406,"color":"amarelo"},
    {"name":"CA08-R12","lat":-16.37935237369245,"lon":-48.98819797057426,"color":"vermelho"},
    {"name":"CA01-R13","lat":-16.37854272958769,"lon":-48.98420846773881,"color":"amarelo"},
    {"name":"CA02-R13","lat":-16.37913416974035,"lon":-48.98275038714663,"color":"amarelo"},
    {"name":"CA03-R13","lat":-16.37930993137917,"lon":-48.98484308001051,"color":"vermelho"},
    {"name":"CA04-R13","lat":-16.37988572845871,"lon":-48.98536768427444,"color":"amarelo"},
    {"name":"CA05-R13","lat":-16.38095279503029,"lon":-48.98491450127794,"color":"amarelo"},
    {"name":"CA06-R13","lat":-16.38062362804156,"lon":-48.98600158701677,"color":"vermelho"},
    {"name":"CA07-R13","lat":-16.38209879481236,"lon":-48.98526073082385,"color":"vermelho"},
    {"name":"CA08-R13","lat":-16.38119256893786,"lon":-48.9868128740574,"color":"amarelo"},
    {"name":"CA04-R14","lat":-16.38029198151941,"lon":-48.97777195479584,"color":"vermelho"},
    {"name":"CA01-R15","lat":-16.37617862165991,"lon":-48.9788025719744,"color":"vermelho"},
    {"name":"CA02-R15","lat":-16.37560454503198,"lon":-48.97987728973892,"color":"vermelho"},
    {"name":"CA03-R15","lat":-16.37433779306125,"lon":-48.9800657394798,"color":"vermelho"},
    {"name":"CA04-R15","lat":-16.3762661447518,"lon":-48.98010038575724,"color":"vermelho"},
    {"name":"CA07-R15","lat":-16.37501092682972,"lon":-48.98115814257993,"color":"vermelho"},
    {"name":"CA08-R15","lat":-16.3753451087264,"lon":-48.98166486494262,"color":"vermelho"},
    {"name":"CA01-R16","lat":-16.36986991431065,"lon":-48.98025999476539,"color":"vermelho"},
    {"name":"CA02-R16","lat":-16.36887839592555,"lon":-48.98167894625406,"color":"vermelho"},
    {"name":"CA01-R17","lat":-16.36920646642718,"lon":-48.97927624162508,"color":"vermelho"},
    {"name":"CA02-R17","lat":-16.37039800831484,"lon":-48.97921311277779,"color":"vermelho"},
    {"name":"CA03-R17","lat":-16.3704102176003,"lon":-48.9778844750914,"color":"vermelho"},
    {"name":"CA02-R18","lat":-16.38245382644863,"lon":-48.97628177237976,"color":"vermelho"},
    {"name":"CA03-R18","lat":-16.37934954338716,"lon":-48.97533453686803,"color":"vermelho"},
    {"name":"CA04-R18","lat":-16.38227185497567,"lon":-48.97524393308203,"color":"vermelho"},
    {"name":"CA05-R18","lat":-16.38100846368664,"lon":-48.97441200658124,"color":"vermelho"},
    {"name":"CA06-R18","lat":-16.37870900002334,"lon":-48.97484471780356,"color":"vermelho"},
    {"name":"CA07-R18","lat":-16.37783048708554,"lon":-48.97647714010557,"color":"vermelho"},
    {"name":"CA08-R18","lat":-16.37569523000405,"lon":-48.97754496047814,"color":"vermelho"},
    {"name":"CA01-R19","lat":-16.37442011393397,"lon":-48.97774849992934,"color":"vermelho"},
    {"name":"CA02-R19","lat":-16.37678946416218,"lon":-48.97636643862133,"color":"vermelho"},
    {"name":"CA03-R19","lat":-16.37425716809687,"lon":-48.97715249830388,"color":"vermelho"},
    {"name":"CA04-R19","lat":-16.37643760650197,"lon":-48.97583445097699,"color":"vermelho"},
    {"name":"CA05-R19","lat":-16.37660560641919,"lon":-48.97511050424046,"color":"vermelho"},
    {"name":"CA06-R19","lat":-16.37315733206934,"lon":-48.97673027020472,"color":"vermelho"},
    {"name":"CA01-R20","lat":-16.38439698808548,"lon":-48.9782714329065,"color":"vermelho"},
    {"name":"CA02-R20","lat":-16.38533826676903,"lon":-48.97968921589079,"color":"vermelho"},
    {"name":"CA04-R20","lat":-16.38331816615592,"lon":-48.98187735976754,"color":"vermelho"},
    {"name":"CA08-R20","lat":-16.38150616996152,"lon":-48.97754834232404,"color":"vermelho"},
    {"name":"CA01-R21-1/16","lat":-16.38477461216138,"lon":-48.97587207439468,"color":"vermelho"},
    {"name":"CA02-R21","lat":-16.38491513825669,"lon":-48.97509913220507,"color":"vermelho"},
    {"name":"CA03-R21","lat":-16.3851726159574,"lon":-48.97386668139308,"color":"vermelho"},
    {"name":"CA04-R21","lat":-16.38650775400902,"lon":-48.97712734366506,"color":"vermelho"},
    {"name":"CA05-R21","lat":-16.38845547810366,"lon":-48.9772333952384,"color":"vermelho"},
    {"name":"CA06-R21-1/16","lat":-16.38810011585025,"lon":-48.97597021748521,"color":"vermelho"},
    {"name":"CA07-R21","lat":-16.38780120309891,"lon":-48.97503765352376,"color":"vermelho"},
    {"name":"CA08-R21","lat":-16.38662822814996,"lon":-48.97368408971393,"color":"vermelho"},
    {"name":"CA01-R22","lat":-16.38712861351355,"lon":-48.98023477342322,"color":"vermelho"},
    {"name":"CA02-R22","lat":-16.38600277451494,"lon":-48.97936564919295,"color":"vermelho"},
    {"name":"CA03-R22","lat":-16.3856145485059,"lon":-48.98115435330474,"color":"vermelho"},
    {"name":"CA08-R22","lat":-16.38683937920607,"lon":-48.9824084402521,"color":"vermelho"},
    {"name":"CA05-R23","lat":-16.39081019810665,"lon":-48.97879085544965,"color":"vermelho"},
    {"name":"CA07-R23","lat":-16.39053268029104,"lon":-48.97769905855602,"color":"vermelho"},
    {"name":"CA08-R23","lat":-16.39026294923395,"lon":-48.97680532053113,"color":"vermelho"},
    {"name":"CA01-R24","lat":-16.39256372600772,"lon":-48.97919883663967,"color":"vermelho"},
    {"name":"CA02-R24","lat":-16.39336984199638,"lon":-48.97905330681665,"color":"vermelho"},
    {"name":"CA03-R24","lat":-16.39181063407555,"lon":-48.97843020386106,"color":"vermelho"},
    {"name":"CA05-R24","lat":-16.39104897393324,"lon":-48.97582604955926,"color":"vermelho"},
    {"name":"CA01-R25","lat":-16.3940425450257,"lon":-48.98136538168919,"color":"vermelho"},
    {"name":"CA02-R25","lat":-16.39444521656212,"lon":-48.98302423439689,"color":"vermelho"},
    {"name":"CA03-R25","lat":-16.39350772067818,"lon":-48.98051153381768,"color":"vermelho"},
    {"name":"CA04-R25","lat":-16.3911142636356,"lon":-48.98005419932962,"color":"vermelho"},
    {"name":"CA05-R25","lat":-16.39089207474019,"lon":-48.9807169551224,"color":"vermelho"},
    {"name":"CA07-R25","lat":-16.39236272201697,"lon":-48.98181307521375,"color":"vermelho"},
    {"name":"CA01-R26","lat":-16.39507964318739,"lon":-48.9812176489286,"color":"vermelho"},
    {"name":"CA02-R26","lat":-16.39654931401845,"lon":-48.98160926995235,"color":"vermelho"},
    {"name":"CA05-R26","lat":-16.39654735055628,"lon":-48.98395885353929,"color":"vermelho"},
    {"name":"CA06-R26","lat":-16.39494863556536,"lon":-48.98366759338555,"color":"vermelho"},
    {"name":"CA07-R26","lat":-16.39669275847862,"lon":-48.98478060154857,"color":"vermelho"},
    {"name":"CA03-R27","lat":-16.39712027071924,"lon":-48.98162584317672,"color":"vermelho"},
    {"name":"CA05-R27","lat":-16.39777915685174,"lon":-48.98574797698048,"color":"vermelho"},
    {"name":"CA06-R27","lat":-16.39595867383946,"lon":-48.98058857386241,"color":"vermelho"},
    {"name":"CA08-R27","lat":-16.39592044493592,"lon":-48.97945467090693,"color":"vermelho"},
    {"name":"CA01-R28","lat":-16.39667645556553,"lon":-48.97875747550832,"color":"vermelho"},
    {"name":"CA03-R28","lat":-16.39819839629196,"lon":-48.97908047886667,"color":"vermelho"},
    {"name":"CA04-R28","lat":-16.40060396627794,"lon":-48.97870732772769,"color":"vermelho"},
    {"name":"CA05-R28","lat":-16.40065152244643,"lon":-48.97919789802821,"color":"vermelho"},
    {"name":"CA06-R28","lat":-16.40223139318036,"lon":-48.97892686309488,"color":"vermelho"},
    {"name":"CA07-R28","lat":-16.4007915652699,"lon":-48.9798363040068,"color":"vermelho"},
    {"name":"CA01-CCV","lat":-16.39810691175334,"lon":-48.96764055449104,"color":"vermelho"},
    {"name":"CA02-CCV","lat":-16.39591270083477,"lon":-48.96427342420894,"color":"vermelho"},
    {"name":"CA01-R29","lat":-16.34880187219262,"lon":-48.97576633586656,"color":"vermelho"},
    {"name":"CA02-R29","lat":-16.34972096225753,"lon":-48.97662903510965,"color":"vermelho"},
    {"name":"CA03-R29","lat":-16.34811969653375,"lon":-48.97622375444752,"color":"vermelho"},
    {"name":"CA04-R29","lat":-16.34785220961602,"lon":-48.97422597014365,"color":"vermelho"},
    {"name":"CA06-R29","lat":-16.34979579578913,"lon":-48.974825,"color":"vermelho"},
    {"name":"CA07-R29","lat":-16.34796197525125,"lon":-48.97303506147156,"color":"vermelho"},
    {"name":"CA08-R29","lat":-16.3490210010038,"lon":-48.97379286540318,"color":"vermelho"},
    {"name":"CA01-R30","lat":-16.34442189343895,"lon":-48.97409024528903,"color":"vermelho"},
    {"name":"CA02-R30","lat":-16.34493214921606,"lon":-48.97297925123576,"color":"vermelho"},
    {"name":"CA03-R30","lat":-16.34615365426657,"lon":-48.97364356680811,"color":"vermelho"},
    {"name":"CA04-R30","lat":-16.34655495200834,"lon":-48.97493383476351,"color":"vermelho"},
    {"name":"CA05-R30","lat":-16.34548800378561,"lon":-48.97248108525833,"color":"vermelho"},
    {"name":"CA06-R30","lat":-16.34594083405295,"lon":-48.97202304876153,"color":"vermelho"},
    {"name":"CA07-R30","lat":-16.34669377403102,"lon":-48.97337013729936,"color":"vermelho"},
    {"name":"CA01-R31","lat":-16.34262901478191,"lon":-48.97736509040372,"color":"vermelho"},
    {"name":"CA04-R31","lat":-16.34461967836545,"lon":-48.9759363162248,"color":"vermelho"},
    {"name":"CA05-R31","lat":-16.34523510281772,"lon":-48.97560913291385,"color":"vermelho"},
    {"name":"CA06-R31","lat":-16.34633579749183,"lon":-48.97627597592396,"color":"vermelho"},
    {"name":"CA07-R31","lat":-16.34541949314195,"lon":-48.97447344405349,"color":"vermelho"},
    {"name":"CA08-R31","lat":-16.34311828466601,"lon":-48.9762303883041,"color":"vermelho"},
    {"name":"CA09-R31","lat":-16.34103096993333,"lon":-48.97671879901164,"color":"vermelho"},
    {"name":"CA01-R32","lat":-16.34293725039633,"lon":-48.97976837957334,"color":"vermelho"},
    {"name":"CA02-R32","lat":-16.34347877684418,"lon":-48.98090010756374,"color":"vermelho"},
    {"name":"CA03-R32","lat":-16.3445962744914,"lon":-48.98058474983193,"color":"vermelho"},
    {"name":"CA04-R32","lat":-16.34402516418187,"lon":-48.9815072868086,"color":"vermelho"},
    {"name":"CA06-R32","lat":-16.34541306557448,"lon":-48.97888537896303,"color":"vermelho"},
    {"name":"CA07-R32","lat":-16.34488862089495,"lon":-48.97943845425365,"color":"vermelho"},
    {"name":"CA08-R32","lat":-16.34491083578925,"lon":-48.97825553499316,"color":"vermelho"},
    {"name":"CA01-R33","lat":-16.34532611539748,"lon":-48.97152260742866,"color":"vermelho"},
    {"name":"CA01-R34","lat":-16.3458657952649,"lon":-48.9706848141243,"color":"vermelho"},
    {"name":"CA05-R37","lat":-16.34355213899221,"lon":-48.97285301607739,"color":"vermelho"},
    {"name":"CA08-R37","lat":-16.34149143733623,"lon":-48.97215085904305,"color":"vermelho"},
    {"name":"CA02-R36","lat":-16.34323760304941,"lon":-48.97005525444411,"color":"vermelho"},
    {"name":"CA03-R36","lat":-16.3408049995429,"lon":-48.96926936866835,"color":"vermelho"},
    {"name":"CA02-R39","lat":-16.33785905046651,"lon":-48.9656075541853,"color":"vermelho"},
    {"name":"CA05-R39","lat":-16.33543919518498,"lon":-48.96295057119765,"color":"vermelho"},
    {"name":"CA08-R39","lat":-16.33749673125401,"lon":-48.96448012933424,"color":"vermelho"},
    {"name":"CA09-R39","lat":-16.33515299845147,"lon":-48.96471724849221,"color":"vermelho"},
    {"name":"CA04-R40","lat":-16.33426169025952,"lon":-48.96111956343423,"color":"vermelho"},
    {"name":"CA06-R41","lat":-16.33303010049988,"lon":-48.95725616078117,"color":"vermelho"},
    {"name":"CA01-R39B","lat":-16.35299276338347,"lon":-48.9870124261859,"color":"vermelho"},
    {"name":"CA02-R39B","lat":-16.35319622835523,"lon":-48.99140601744797,"color":"vermelho"},
    {"name":"CA03-R39B","lat":-16.35146962921354,"lon":-48.99245012983055,"color":"vermelho"},
    {"name":"CA04-R39B","lat":-16.3494318640456,"lon":-48.98583327308839,"color":"vermelho"},
    {"name":"CA05-R39B","lat":-16.34845117184411,"lon":-48.98414315590919,"color":"vermelho"},
    {"name":"CA06-R39B","lat":-16.34872106695919,"lon":-48.98649214637447,"color":"vermelho"},
    {"name":"CA07-R39B","lat":-16.34768012046808,"lon":-48.9852638091846,"color":"vermelho"},
    {"name":"CA08-R39B","lat":-16.34678936155007,"lon":-48.98415463616429,"color":"vermelho"},
    {"name":"CA09-R39B","lat":-16.34831342696252,"lon":-48.99076048281499,"color":"vermelho"},
    {"name":"CA10-R39B","lat":-16.35418349731928,"lon":-48.98844383211779,"color":"vermelho"},
    {"name":"CA11-R39B","lat":-16.34695037604037,"lon":-48.98375047439619,"color":"vermelho"},
]

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = math.sin(d_lat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def parse_coords(text):
    """Extrai coordenadas de link Google Maps ou texto com lat,lon."""
    patterns = [
        r'@(-?\d+\.\d+),(-?\d+\.\d+)',
        r'\?q=(-?\d+\.\d+),(-?\d+\.\d+)',
        r'll=(-?\d+\.\d+),(-?\d+\.\d+)',
        r'place/(-?\d+\.\d+),(-?\d+\.\d+)',
        r'maps/(-?\d+\.\d+),(-?\d+\.\d+)',
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return float(m.group(1)), float(m.group(2))
    # coordenadas diretas
    m = re.search(r'(-?\d+\.\d+)[,\s]+(-?\d+\.\d+)', text)
    if m:
        a, b = float(m.group(1)), float(m.group(2))
        if abs(a) < 90 and abs(b) < 180:
            return a, b
    return None, None

async def geocode_address(address):
    """Geocodifica endereço via Nominatim."""
    url = f"https://nominatim.openstreetmap.org/search?q={address}&format=json&limit=1"
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url, headers={"User-Agent": "i2FibraBot/1.0"})
        data = r.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    return None, None

async def ors_distance(lat1, lon1, lat2, lon2):
    """Distância por rua via OpenRouteService."""
    url = (
        f"https://api.openrouteservice.org/v2/directions/foot-walking"
        f"?api_key={ORS_KEY}&start={lon1},{lat1}&end={lon2},{lat2}"
    )
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(url)
        if r.status_code == 200:
            data = r.json()
            return data["features"][0]["properties"]["segments"][0]["distance"]
    return None

def status_emoji(color):
    return {"vermelho": "🔴", "amarelo": "🟡", "verde": "🟢"}.get(color, "⚪")

def status_label(color):
    return {"vermelho": "Ativa", "amarelo": "Implantação", "verde": "Projeto"}.get(color, "?")

# ─── ANÁLISE PRINCIPAL ────────────────────────────────────────────────────────
async def analisar_viabilidade(lat, lon):
    """Retorna dict com resultado da viabilidade."""
    # Pré-filtro linha reta
    candidatos = [
        {**c, "dist_reta": haversine(lat, lon, c["lat"], c["lon"])}
        for c in CTOS
    ]
    candidatos = sorted(candidatos, key=lambda x: x["dist_reta"])
    candidatos_proximos = [c for c in candidatos if c["dist_reta"] <= RAIO_FILTRO][:MAX_CTOS]

    if not candidatos_proximos:
        mais_prox = candidatos[0] if candidatos else None
        return {"viavel": False, "motivo": "fora_area", "mais_proxima": mais_prox}

    usar_ors = bool(ORS_KEY)
    resultados = []

    if usar_ors:
        for c in candidatos_proximos:
            dist_rua = await ors_distance(lat, lon, c["lat"], c["lon"])
            resultados.append({**c, "dist_rua": dist_rua})
            await asyncio.sleep(0.4)  # gentil com a API
        resultados.sort(key=lambda x: (x["dist_rua"] or 99999))
        dentro = [r for r in resultados if r["dist_rua"] is not None and r["dist_rua"] <= LIMITE_ROTA]
    else:
        resultados = candidatos_proximos
        dentro = [r for r in resultados if r["dist_reta"] <= LIMITE_ROTA]

    return {
        "viavel": len(dentro) > 0,
        "usar_ors": usar_ors,
        "dentro": dentro,
        "candidatos": resultados,
        "lat": lat,
        "lon": lon,
    }

def formatar_resultado(res, data_hora):
    """Formata a mensagem de resposta do bot."""
    lat, lon = res["lat"], res["lon"]
    maps_url = f"https://maps.google.com/?q={lat},{lon}"
    metodo = "por rua (ORS)" if res.get("usar_ors") else "linha reta estimada"

    linhas = [
        "━━━━━━━━━━━━━━━━━━━━━━",
        "📡 *VIABILIDADE — i2 Fibra*",
        "━━━━━━━━━━━━━━━━━━━━━━",
        f"📅 {data_hora}",
        f"📍 `{lat:.6f}, {lon:.6f}`",
        f"🗺️ [Ver no Maps]({maps_url})",
        f"📐 Método: {metodo}",
        "",
    ]

    if res.get("motivo") == "fora_area":
        linhas += ["❌ *INVIÁVEL — fora da área de cobertura*", ""]
        if res.get("mais_proxima"):
            mp = res["mais_proxima"]
            linhas.append(f"CTO mais próxima: *{mp['name']}* a ~{mp['dist_reta']:.0f}m")
    elif res["viavel"]:
        melhor = res["dentro"][0]
        dist = melhor.get("dist_rua") or melhor.get("dist_reta")
        linhas += [
            "✅ *VIÁVEL*",
            "",
            f"📦 CTO: *{melhor['name']}*",
            f"📏 Distância: *{dist:.0f}m* {metodo}",
            f"🔵 Status: {status_emoji(melhor['color'])} {status_label(melhor['color'])}",
            f"🎯 CTOs ≤ 300m: {len(res['dentro'])}",
        ]
        if len(res["dentro"]) > 1:
            linhas.append("")
            linhas.append("_Outras CTOs próximas:_")
            for c in res["dentro"][1:4]:
                d = c.get("dist_rua") or c.get("dist_reta")
                linhas.append(f"  {status_emoji(c['color'])} {c['name']} — {d:.0f}m")
        linhas += ["", "✔️ Cliente pode ser atendido."]
    else:
        mais_prox = res["candidatos"][0] if res["candidatos"] else None
        linhas += ["❌ *INVIÁVEL — sem CTO em 300m*", ""]
        if mais_prox:
            d = mais_prox.get("dist_rua") or mais_prox.get("dist_reta")
            linhas.append(f"CTO mais próxima: *{mais_prox['name']}* a {d:.0f}m")
        linhas += ["", "⚠️ Necessário instalar nova CTO."]

    linhas.append("━━━━━━━━━━━━━━━━━━━━━━")
    return "\n".join(linhas)

# ─── HANDLERS TELEGRAM ────────────────────────────────────────────────────────
def is_owner(update: Update) -> bool:
    return update.effective_user.id == OWNER_ID

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return
    msg = (
        "👋 *Bot de Viabilidade i2 Fibra*\n\n"
        "Manda qualquer um destes:\n"
        "• 🔗 Link do Google Maps\n"
        "• 📍 Coordenadas: `-16.35, -48.97`\n"
        "• 📌 Localização pelo Telegram (botão 📎)\n\n"
        f"Rede carregada: *{len(CTOS)} CTOs*\n"
        f"Método: *{'ORS (distância por rua)' if ORS_KEY else 'linha reta'}*"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return
    await update.message.reply_text(
        f"✅ Bot online\n"
        f"CTOs: {len(CTOS)}\n"
        f"ORS: {'✅ configurado' if ORS_KEY else '⚠️ não configurado (usando linha reta)'}"
    )

async def handle_location(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Trata localização enviada pelo Telegram."""
    if not is_owner(update):
        return
    loc = update.message.location
    await processar(update, loc.latitude, loc.longitude)

async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Trata texto com link ou coordenadas."""
    if not is_owner(update):
        return
    text = update.message.text.strip()

    # Tenta extrair coordenadas direto
    lat, lon = parse_coords(text)

    # Se não achou, tenta geocodificar como endereço
    if lat is None:
        msg = await update.message.reply_text("⏳ Buscando endereço...")
        lat, lon = await geocode_address(text)
        await msg.delete()

    if lat is None:
        await update.message.reply_text(
            "❌ Não consegui identificar a localização.\n\n"
            "Tente:\n• Link do Google Maps\n• Coordenadas: `-16.35, -48.97`\n• Compartilhar localização pelo Telegram",
            parse_mode="Markdown"
        )
        return

    await processar(update, lat, lon)

async def processar(update: Update, lat: float, lon: float):
    """Processa a análise e responde."""
    msg = await update.message.reply_text("⏳ Analisando viabilidade...")
    try:
        resultado = await analisar_viabilidade(lat, lon)
        data_hora = datetime.now().strftime("%d/%m/%Y %H:%M")
        texto = formatar_resultado(resultado, data_hora)
        await msg.edit_text(texto, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        await msg.edit_text(f"❌ Erro na análise: {str(e)}")

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(MessageHandler(filters.LOCATION, handle_location))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("🤖 Bot i2 Fibra iniciado!")
    app.run_polling()

if __name__ == "__main__":
    main()
