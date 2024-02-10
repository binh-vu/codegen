from dataclasses import dataclass


@dataclass
class Resource:
    id: str
    type: str


@dataclass
class AttrDim:
    value: tuple[int, int | None] | int | str

    def is_range(self):
        return isinstance(self.value, (tuple, list))


@dataclass
class Attr:
    name: str
    resource: str
    location: list[AttrDim]

    @staticmethod
    def from_dict(o: dict):
        return Attr(o["name"], o["resource"], [AttrDim(x) for x in o["path"]])


@dataclass
class DRepr:
    resources: dict[str, Resource]
    attrs: dict[str, Attr]
    # aligned dimensions between attrs
    alignments: dict[tuple[str, str], list[tuple[int, int]]]
    subj: str
    props: dict[str, str]

    @staticmethod
    def from_dict(o: dict):
        return DRepr(
            resources={v["id"]: Resource(**v) for v in o["resources"]},
            attrs={v["name"]: Attr.from_dict(v) for v in o["attrs"]},
            alignments={
                (x["source"], x["target"]): [tuple(x1) for x1 in x["dims"]]
                for x in o["alignments"]
            },
            subj=o["subj"],
            props=o["props"],
        )
