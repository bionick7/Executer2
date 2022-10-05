import random
from message_processing import data


class NameGenerator:
    def __init__(self, namelist_path: str):
        self.name_data: dict[str, list[str]] = {}

        current_text_list_name = ""
        with open(namelist_path) as f:
            lines = f.readlines()
            for line in lines:
                if line.startswith("@"):
                    current_text_list_name = line[2:].strip()
                    self.name_data[current_text_list_name] = []
                elif current_text_list_name in self.name_data and line.strip() != "":
                    self.name_data[current_text_list_name].append(line.strip())

        self.name_templates = self.name_data.get("name templates", "<NAME T>")
        self.ship_templates = self.name_data.get("ship templates", "<SHIP T>")

        self.nouns = self.name_data.get("nouns", ["<NOUN>"])
        self.adjectives = self.name_data.get("adjectives", ["<ADJ"])
        self.prefixes = self.name_data.get("prefixes", ["<PRFX>"])
        self.first_names = self.name_data.get("firstnames", ["<FIRSTN>"])
        self.surnames = self.name_data.get("surnames", ["<SURN>"])
        self.onsets = self.name_data.get("onset clusters", ["<ONSET>"])[0].split("|")
        self.nuclei = self.name_data.get("nuclei", ["<NUCLEUS>"])[0].split("|")
        self.coda = self.name_data.get("coda clusters", ["<CODUM>"])[0].split("|")

    def gen_person_name(self) -> str:
        return self.gen_name_from_template(self.name_templates)

    def gen_ship_name(self) -> str:
        return self.gen_name_from_template(self.ship_templates)

    def gen_word(self, syllable_count: int = -1) -> str:
        if syllable_count == -1:
            syllable_count = random.randint(2, 5)
        res = self.gen_syllable()
        for i in range(syllable_count):
            next = self.gen_syllable()
            if res != "" and next != "":
                if next[0] in "iueoa" and res[-1] in "iueoa":
                    res += random.choice(self.onsets)
            res += next
        return res

    def gen_syllable(self) -> str:
        res = random.choice(self.nuclei)
        if random.random() < 0.6:
            res = random.choice(self.onsets) + res
        if random.random() < 0.4:
            res += random.choice(self.coda)
        return res

    def _replace_in_name(self, code: str) -> str:
        res = ""
        if code.upper() == "NOUN":
            res, *_ = random.choice(self.nouns).split(",")
        if code.upper() == "ADJ":
            res = random.choice(self.adjectives)
        if code.upper() == "PREF":
            res = random.choice(self.prefixes)
        if code.upper() == "FIRSTNAME":
            res = random.choice(self.first_names)
        if code.upper() == "SURNAME":
            res = random.choice(self.surnames)
        if code.upper() == "NAME":
            res = self.gen_person_name()
        if code.upper() == "SHIP":
            res = self.gen_ship_name()
        if code.upper() == "GEN":
            res = self.gen_word()
        if code == "" or res == "":
            return "???"
        if code[0].isupper():
            return res.capitalize()
        else:
            return res

    def _choose_template(self, templates: list[str]) -> str:
        weighted_templates: list[(str, float)] = []
        for template_index, template in enumerate(templates):
            start = -1
            num = 1
            i = 0
            for c in template:
                if c == "{":
                    start = i + 1
                if c == "}" and start != -1:
                    macro = template[start: i]
                    injection = macro
                    if macro.isdigit():
                        num = int(macro)
                        injection = ""
                    elif macro.startswith("?"):
                        injection = macro[1:] if random.random() > 0.5 else ""
                    elif "|" in macro:
                        options = macro.split("|")
                        injection = random.choice(options)
                    # print(template, "---", start, i, injection, template[:start-1] + injection + template[i+1:])
                    template = template[:start-1] + injection + template[i+1:]
                    i = i - len(macro) + len(injection) - 2
                    start = -1
                i += 1
            weighted_templates.append((template.strip(), num))
        return self._choose_weighted(weighted_templates)

    def gen_name_from_template(self, templates: list[str]) -> str:
        template = self._choose_template(templates)
        start = -1
        res = ""
        for i, c in enumerate(template):
            if c == "[":
                start = i+1
            if start == -1:
                res += c
            if c == "]" and start != -1:
                code = template[start: i]
                res += self._replace_in_name(code)
                start = -1
        return res

    @staticmethod
    def _choose_weighted(weighted_list: list[(any, float)]) -> any:
        objs, weights = zip(*weighted_list)
        d = random.random() * sum(weights)
        acc = 0
        for i in range(len(weighted_list)):
            acc += weights[i]
            if d < acc:
                return objs[i]
        # Shouldn't be reached
        print("Should not be reached")
        return objs[-1]


name_generator = NameGenerator(data["config"]["namesgen_path"])

if __name__ == "__main__":
    random.seed(0)
    # Testing
    for i in range(10):
        print(name_generator.gen_ship_name())
    for i in range(10):
        print(name_generator.gen_person_name())
    for i in range(10):
        print(name_generator.gen_word())
