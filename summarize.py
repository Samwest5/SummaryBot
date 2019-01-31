import wikipedia


def get_summary(topic):
    return wikipedia.summary(topic)

def get_hits(topic):
    return wikipedia.search(topic)






