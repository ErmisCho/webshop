from django import forms


class InquiryForm(forms.Form):
    name = forms.CharField(required=False)
    email = forms.EmailField()
    phone = forms.CharField(required=False)
    message = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"rows": 3}))

    order_number = forms.CharField(required=False, widget=forms.HiddenInput())
    order_note = forms.CharField(required=False, widget=forms.HiddenInput())
