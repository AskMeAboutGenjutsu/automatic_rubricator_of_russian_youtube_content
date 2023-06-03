def get_vector(w2v, token):
    try:
        return w2v.get_vector(token)
    except KeyError:
        return []