from mincult.org_creator import update_orgs


def bulk_update_orgs():
    def read_update_orgs_from_file():
        exist_orgs = dict()
        file_name = "update.txt"
        try:
            with open(file_name) as f:
                for line in f:
                    date, min_id, even_id = line.strip().split(' ')
                    exist_orgs[int(min_id)] = int(even_id)
        except IOError:
            pass
        return exist_orgs

    org_ids = read_update_orgs_from_file()
    update_orgs(org_ids)


bulk_update_orgs()
