from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        # Disconnect last_login signal to allow read-only SQLite on Vercel
        # (Re-enabling it implicitly by just not disconnecting it if we have Postgres, 
        # but let's keep it clean and use our own notification signal)
        from django.contrib.auth.signals import user_logged_in
        from django.db.models.signals import post_save
        from django.dispatch import receiver
        from django.core.mail import send_mail
        from django.conf import settings
        from .models import CustomUser

        @receiver(post_save, sender=CustomUser)
        def notify_admin_on_signup(sender, instance, created, **kwargs):
            if created:
                subject = f"New User Registered: {instance.username}"
                message = f"User {instance.username} ({instance.email}) has created an account as {instance.role}."
                try:
                    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [settings.EMAIL_HOST_USER])
                except Exception as e:
                    print(f"Failed to send signup email: {e}")

        @receiver(user_logged_in)
        def notify_admin_on_login(sender, request, user, **kwargs):
            subject = f"User Login Notification: {user.username}"
            message = f"User {user.username} has just logged into the portal."
            try:
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [settings.EMAIL_HOST_USER])
            except Exception as e:
                print(f"Failed to send login email: {e}")

