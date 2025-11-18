from django.shortcuts import render


def custom_404(request, exception):
  """
  Render a friendly 404 page instead of the default debug message when DEBUG=False.
  """
  return render(request, '404.html', status=404, context={
    'requested_path': request.path,
  })
