import wget


def download_song(file_name):
    count = 1

    temp_file = open("temp " + file_name, "a+")

    with open(file_name, "r") as f:
        for line in f:
            if line not in temp_file:
                wget.download(line)
                temp_file.write(line)
                print(f"{count} songs downloaded")
                count += 1
            else:
                print("song already downloaded")

    temp_file.close()


if __name__ == "__main__":
    download_song("naomi raine.txt")
