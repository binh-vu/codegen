import json

from codegen.models import AST, Memory, PredefinedFn, Var, expr
from drepr.prelude import Alignment, BaseWriter, DRepr
from drepr.varspace import VarSpace
from drepr.writers import TTLWriter

with open("./data.json", "r") as f:
    dmod = DRepr.from_dict(json.load(f))


ast = AST.root()
mem = Memory()

main_fn = ast.func(
    "main",
    [Var.create(mem, f"resource_{res.id}") for res in dmod.resources.values()],
)

writer = TTLWriter(main_fn, mem)
alignment = Alignment(dmod)

for resource in dmod.resources.values():
    var = Var.create(
        mem, f"resource_data_{resource.id}", key=VarSpace.resource_data(resource.id)
    )
    main_fn.assign(
        var,
        expr.ExprFuncCall(
            expr.ExprIdent(f"read_source_{resource.type}"),
            [expr.ExprVar(Var.deref(mem, name=f"resource_{resource.id}"))],
        ),
    )

    def loop_subj_attr(block: AST, obj, depth: int, prev_vars: list[Var]):
        if depth >= len(obj["location"]):
            return None

        if depth == 0:
            collection = obj["collection"]
        else:
            collection = prev_vars[-1]

        dim = obj["location"][depth]
        while not dim.is_range() and depth < len(obj["location"]) - 1:
            c1 = Var.create(mem, name=f"value_{depth}")
            block.assign(
                c1, PredefinedFn.item_getter(expr.ExprVar(collection), dim.value)
            )
            collection = c1
            depth += 1
            dim = obj["location"][depth]

        assert dim.is_range(), (dim, depth)
        start_var = Var.create(mem, f"start_{depth}")
        block.assign(start_var, expr.ExprConstant(dim.value[0]))

        end_var = Var.create(mem, f"end_{depth}")
        if dim.value[1] is None:
            block.assign(end_var, PredefinedFn.len(expr.ExprVar(collection)))
        else:
            block.assign(end_var, expr.ExprConstant(dim.value[1]))

        itemindex = Var.create(
            mem,
            f"index_{depth}",
            key=VarSpace.attr_index_dim(obj["resource"], obj["name"], depth),
        )
        subblock = block.for_loop(
            item=itemindex,
            iter=PredefinedFn.range(expr.ExprVar(start_var), expr.ExprVar(end_var)),
        )
        itemvalue = Var.create(
            mem,
            f"value_{depth}",
            key=VarSpace.attr_value_dim(obj["resource"], obj["name"], depth),
        )
        subblock.assign(
            itemvalue,
            PredefinedFn.item_getter(expr.ExprVar(collection), expr.ExprVar(itemindex)),
        )

        # handle the case where the remaining depth is all non-range
        if depth + 1 < len(obj["location"]) and all(
            not d.is_range() for d in obj["location"][depth + 1 :]
        ):
            for _ in range(len(obj["location"]) - depth - 1):
                depth += 1
                itemvalue = Var.create(
                    mem,
                    f"value_{depth}",
                    key=VarSpace.attr_value_dim(obj["resource"], obj["name"], depth),
                )
                subblock.assign(
                    itemvalue,
                    PredefinedFn.item_getter(
                        expr.ExprVar(itemvalue),
                        expr.ExprConstant(obj["location"][depth].value),
                    ),
                )
        return subblock, depth + 1, (itemvalue,)

    main_fn.linebreak()
    main_fn.comment("Loop through elements in the subject attribute")
    inner_subj_loop, subj_loop_vars = main_fn.nested_stmts(
        loop_subj_attr,
        obj={
            "name": dmod.subj,
            "location": dmod.attrs[dmod.subj].location,
            "collection": Var.deref(
                mem, name=f"resource_data_{dmod.attrs[dmod.subj].resource}"
            ),
            "resource": dmod.attrs[dmod.subj].resource,
        },
    )

    writer.create_record(inner_subj_loop)
    writer.add_subject(inner_subj_loop, expr.ExprVar(subj_loop_vars[-1][-1]))

    def loop_remain_attr(prog: AST, obj, index: int):
        if index >= len(obj["props"]):
            return None

        prop, attr = obj["props"][index]
        # convert subject index into attr index
        # get the value of the attribute
        # then add it into the writer.
        if alignment.is_one_to_one_alignment(dmod.attrs[dmod.subj], dmod.attrs[attr]):
            attr_value = alignment.get_one_to_one(
                dmod.attrs[dmod.subj], dmod.attrs[attr], mem, prog
            )
        else:
            raise NotImplementedError()

        writer.add_property(prog, prop, expr.ExprVar(attr_value))

    # the loop should support break, etc.
    inner_subj_loop.seq_stmts(loop_remain_attr, obj={"props": list(dmod.props.items())})
    writer.commit_record(inner_subj_loop)

writer.finish(main_fn)
print(ast.to_python())
