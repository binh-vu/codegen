from codegen.models import AST, Memory, Var, expr
from drepr.models import Attr, DRepr
from drepr.varspace import VarSpace


class Alignment:

    def __init__(self, model: DRepr):
        self.model = model

    def is_one_to_one_alignment(self, subj: Attr, obj: Attr):
        """Test if the alignment is one-to-one."""
        print(
            set(tdi for sdi, tdi in self.model.alignments[subj.name, obj.name]),
            set(di for di, dim in enumerate(obj.location) if dim.is_range()),
        )
        return set(
            tdi for sdi, tdi in self.model.alignments[subj.name, obj.name]
        ) == set(di for di, dim in enumerate(obj.location) if dim.is_range())

    def get_one_to_one(self, source: Attr, target: Attr, mem: Memory, prog: AST):
        """This function generates code to retrieve target index assigned to some variables."""
        target_dims = []
        for di, dim in enumerate(target.location):
            if dim.is_range():
                # make sure that is has been aligned with the subj.
                source_di = self._get_align_dim(source, target, di)
                target_dims.append(source_di)
            else:
                target_dims.append(dim.value)

        # generate code to retrieve the target index
        for di, dim in enumerate(target.location):
            # we create a variable that hold the value of this dimension -- note that this can be optimized away later
            target_dim = Var.create(
                mem,
                f"{target.name}_index_dim_{di}",
                key=VarSpace.attr_index_dim(target.resource, target.name, di),
            )
            if not dim.is_range():
                prog.assign(target_dim, expr.ExprConstant(dim.value))

            else:
                source_di = self._get_align_dim(source, target, di)
                prog.assign(
                    target_dim,
                    expr.ExprVar(
                        Var.deref(
                            mem,
                            key=VarSpace.attr_index_dim(
                                source.resource,
                                source.name,
                                source_di,
                            ),
                        )
                    ),
                )

            if di == 0:
                parent_target_value = Var.deref(
                    mem, key=VarSpace.resource_data(target.resource)
                )
            else:
                parent_target_value = Var.deref(
                    mem,
                    key=VarSpace.attr_value_dim(target.resource, target.name, di - 1),
                )
            target_value = Var.create(
                mem,
                f"{target.name}_value_dim_{di}",
                key=VarSpace.attr_value_dim(target.resource, target.name, di),
            )
            if not dim.is_range():
                prog.assign(
                    target_value,
                    expr.PredefinedFn.item_getter(
                        expr.ExprVar(parent_target_value),
                        expr.ExprConstant(dim.value),
                    ),
                )
            else:
                prog.assign(
                    target_value,
                    expr.PredefinedFn.item_getter(
                        expr.ExprVar(parent_target_value),
                        expr.ExprVar(
                            Var.deref(
                                mem,
                                key=VarSpace.attr_index_dim(
                                    source.resource,
                                    source.name,
                                    source_di,
                                ),
                            )
                        ),
                    ),
                )
        return target_value

    def _get_align_dim(self, source: Attr, target: Attr, target_dim: int):
        for sid, tid in self.model.alignments[source.name, target.name]:
            if tid == target_dim:
                return sid
        assert False
