from django.db.models import Model, CASCADE, ForeignKey, BooleanField, DateTimeField
from apps.users.models import CustomUser as User
from apps.blog.models import Comment


class Notification(Model):
    recipient = ForeignKey(User, on_delete=CASCADE, related_name="notifications")
    comment = ForeignKey(Comment, on_delete=CASCADE, related_name="notifications")
    is_read = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)
