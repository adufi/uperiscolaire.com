import jwt

from datetime import datetime, timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand

from users.models import User


class Command(BaseCommand):
    help = 'Recall for parents with non verified email'

    def register_send_mail(self, id, email):
        token = self._encode_activation_token(id)
        # https://uperiscolaire.com/verify/{}/
        message = '''Bonjour,

Pour finaliser votre inscription au nouveau service en ligne de L'U.P.E.E.M., veuillez confirmer votre adresse email en cliquant sur le lien suivant:

https://uperiscolaire.com/verify/{}/

Service Périscolaire de l'UPEEM.

(*) Ce lien d'activation n'est valable que pour une durée de 7 jours.
    
En cas de difficultés, merci de nous contacter au 0596 70 32 54.
Cordialement,
L'équipe UPEEM ACM.'''.format(token)

        try:
            send_mail(
                'Rappel: Activation de votre compte',
                message,
                'UPEEM (Ne pas répondre) <noreply@upeem.org>',
                [email]
            )
        except Exception as e:
            print ('register_send_mail() An exception occured with error: ' + str(e))

    def _encode_activation_token(self, id):
        """Generates the auth token"""
        try:
            payload = {
                'exp':
                    datetime.utcnow() + timedelta(
                        days=settings.EMAIL_VERIFICATION_EXPIRATION_DAYS,
                        seconds=settings.EMAIL_VERIFICATION_EXPIRATION_SECONDS
                    ),
                # 'iat': datetime.utcnow(),
                'id': id,
                'type': 'email_activation'
            }
            token = jwt.encode(
                payload,
                settings.SECRET_KEY,
                algorithm='HS256'
            )
            return token.decode('utf-8')
        except Exception as e:
            return e


    def _decode_activation_token(self, auth_token):
        """
        Decodes the auth token - :param auth_token: - :return: integer|string
        """
        try:
            payload = jwt.decode(
                auth_token, 
                settings.SECRET_KEY
            )
            payload_type = payload.get('type', False)
            if not payload_type or payload_type != 'email_activation':
                return 'Invalid payload type.'
            return payload['id']
        except jwt.ExpiredSignatureError:
            return 'Signature expired. Please log in again.'
        except jwt.InvalidTokenError:
            return 'Invalid token. Please log in again.'


    def run (self):
        emails = [
            # 'stephie.mc-d@live.fr',
            # 'laurencinfeliciaa972@hotmail.fr',
            'stensaintlouis@yahoo.fr',
            # 'megane.montrop@gmail.com',
            # 'djayannokk972@icloud.com',
            # 'lesmalaya@msn.com',
            # 'kanelliac97212@gmail.com',
            # 'fontaineursula20@gmail.com',
            # 'sandrinesaina@gmail.com',
            # 'merlin_maud2@yahoo.fr',
            # 'fourlin.elisa@gmail.com',
            # 'arielle-deriau@hotmail.fr',
            # 'andrea.quiquine@hotmail.fr',
            # 'katussia1308@gmail.com',
            # 'sandracardou2@gmail.com',
            # 'giovanna.victor.gv@hotmail.com',
            'dorfeansmeline122405@gmail.com',
            # 'gouacidea@gmail.com',
            # 'bardoux-samantha@outlook.com',
            # 'fabien.jeanbolo@gmail.com',
            # 'claudinebeaunol@gmail.com',
            # 'kathleen.singamalum@gmail.com',
            # 'sandrinethimon@outlook.fr',
            # 'naomiemariesainte@yahoo.fr',
            # 'michaeljo972@gmail.com',
            # 'lynda.cyrille04@gmail.com',
            # 'kristencharlesangele@hotmail.com',
            # 'ba.nemo27@gmail.com',
            # 'dominik9713@outlook.fr',
            # 'nathalieprintempsmathieu@orange.fr',
            'jplagb@gmail.com',
            # 'isaora12@gmail.com',
            # 'will-and-soso@hotmail.fr',
            # 'maryamelie.narcissot@gmail.com',
            # 'laurence.97212@hotmail.fr',
            # 'v.agasseau@gmail.com',
            # 'aradejaina@hotmail.fr',
            # 'petitenanou@protonmail.com',
            # 'myriambonose@laposte.net',
            # 'lilet.bouhot@wanadoo.fr',
            # 'anne-sophie97212@hotmail.fr',
            # 'catyou972@hotmail.fr',
            # 'regasandra58@gmail.com',
            # 'marielucejeanmichel@gmail.com',
            # 'maelann79@gmail.com',
            # 'harry.bedouin@gmail.com',
            # 'berniacstephane@yahoo.fr',
            # 'numu33@yahoo.fr',
            # 'macrislimmois@gmail.com',
            # 'zezettedocha@gmail.com',
            # 'sohan97212@gmail.com',
            # 'celinecaclin@gmail.com',
            # 'laetu972@gmail.com',
            # 'v.mouflard@laposte.net',
            # 'oliviafonrose972@gmail.com',
            'kindih972@gmail.com',
            # 'touche.johana@gmail.com',
            # 'priscillia.couturier@gmail.com',
            # 'isa.lepel971@gmail.com',
            'meneusjohnny@gmail.com',
            # 'm.darragon@laposte.net',
            # 'karenduroselle414@gmail.com',
            # 'plocussamantha@gmail.com',
            # 'kettylipan@gmail.com',
            # 'dinandi62@gmail.com',
            # 'celinebellance16@gmail.com',
            # 'seamansuzy972@gmail.com',
            # 'melissabeaunol@outlook.fr',
            # 'claudiaj-arnaud@hotmail.fr',
            # 'valerie.vellaidon@live.fr',
            # 'johannealonzeau@gmail.com',
            # 'audrey.mastail@gmail.com',
            # 'celiadaniel193@gmail.com',
            # 'vanilloane.972@hotmail.com',
            # 'linda.dan@hotmail.fr',
            'touche.victoria@outlook.fr',
            # 'golvatkatarina@gmail.com',
            # 'minger_ingrid@live.fr',
            # 'lebruncoralie972@gmail.com',
            # 'manuel.gentil.mg@gmail.com',
            # 'me.baubant@laposte.net',
            # 'felynab@outlook.com',
            # 'l.arlette-972@outlook.fr',
            # 'mzllemayou8@gmail.com',
            # 'lynda.christine@orange.fr',
            # 'edenbelliard@gmail.com',
            # 'nehelie77@gmail.com',
            # 'david.serine@gmail.com',
            # 'valentinastrid0@gmail.com',
            # 'annesophierupert@gmail.com',
            # 'denise.londas@hotmail.com',
            # 'katouvanou@hotmail.fr',
            # 'milton.bettina@hotmail.fr',
            # 'constance.laval@gmail.com',
            # 'dadou9721@live.fr',
            # 'golvetclementine@gmail.com',
            # 'maudrinebeauvais@gmail.com',
            # 'sylvia.quiquine@outlook.fr',
            'patrice.lorfeuvre@gmail.com',
            # 'ludivine.lillo@gmail.com',
            # 'inlor97212stjo@gmail.com',
            # 'soliman.polina@gmail.com',
            # 'alice.megange@hotmail.fr',
            # 'luana-972@hotmail.com',
            # 'michou.mn66@gmail.com',
            # 'elodiehartock7@gmail.com',
        ]

        # emails = [
        #     'jessica.clement.972@orange.fr',
        #     'arnaud.angely@gmail.com',
        # ]

        for email in emails:
            try:
                user = User.objects.get(auth__email=email)
                self.register_send_mail(user.id, email)
            except User.DoesNotExist:
                print (f'User not found for email: {email}')


    def test (self):
        user = User.objects.get(auth__email='jessica.clement.972@orange.fr')
        # user = User.objects.get(auth__email='sys.admin@mail.fr')
        token = self._encode_activation_token(user.id)
        print (f'https://uperiscolaire.com/verify/{token}/')

    def handle(self, *args, **kwargs):
        self.run()
        # self.test()