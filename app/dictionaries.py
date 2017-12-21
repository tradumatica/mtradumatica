
def search_dictionary(filename, word):
  pattern = " " + word + " "
  results = []
  with open(filename, "r") as f:
    for line in f:
      if line.find(pattern) != -1:
        p = line.split(pattern)
        results.append((p[0], float(p[1])))

  results.sort(key=lambda x: x[1], reverse=True)
  return results
