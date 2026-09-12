from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin

from freight.api.v1.serializers.dispatch import (
    DispatchAssignDispatcherSerializer,
    DispatchBatchCreateSerializer,
    DispatchBatchSerializer,
    DispatchDeliveredSerializer,
    DispatchFreightAssignmentCreateSerializer,
    DispatchFreightAssignmentSerializer,
    DispatchOrderCreateSerializer,
    DispatchOrderSerializer,
    DispatchRejectSerializer,
    DispatchStatusSerializer,
)
from freight.models import (
    Branch,
    DispatchBatch,
    DispatchFreightAssignment,
    DispatchOrder,
    FreightCompany,
    ShipmentOrder,
)
from freight.services.dispatch_service import (
    add_order_to_batch,
    approve_dispatch_handover,
    assign_dispatcher,
    assign_freight_company,
    cancel_dispatch_batch,
    cancel_dispatch_order,
    cancel_freight_assignment,
    complete_dispatch_batch,
    create_dispatch_batch,
    get_order_freight_amount,
    make_batch_ready,
    mark_freight_assignment_delivered,
    reject_dispatch_order,
    remove_order_from_batch,
    return_dispatch_order,
    start_dispatch,
)


def get_dispatch_batch_for_user(batch_id, user):
    queryset = (
        DispatchBatch.objects
        .select_related(
            "branch",
            "dispatcher",
            "created_by",
        )
        .prefetch_related(
            "orders__order",
            "orders__freight_assignments__freight_company",
            "orders__freight_assignments__created_by",
        )
    )

    if not user.is_superuser:
        queryset = queryset.filter(
            branch=user.branch
        )

    return get_object_or_404(
        queryset,
        pk=batch_id,
    )


def get_dispatch_order_for_user(dispatch_order_id, user):
    queryset = (
        DispatchOrder.objects
        .select_related(
            "batch",
            "batch__branch",
            "batch__dispatcher",
            "order",
            "order__customer",
        )
        .prefetch_related(
            "freight_assignments__freight_company",
            "freight_assignments__created_by",
        )
    )

    if not user.is_superuser:
        queryset = queryset.filter(
            batch__branch=user.branch
        )

    return get_object_or_404(
        queryset,
        pk=dispatch_order_id,
    )


def get_dispatch_assignment_for_user(assignment_id, user):
    queryset = (
        DispatchFreightAssignment.objects
        .select_related(
            "dispatch_order",
            "dispatch_order__batch",
            "dispatch_order__batch__branch",
            "dispatch_order__order",
            "freight_company",
            "created_by",
        )
    )

    if not user.is_superuser:
        queryset = queryset.filter(
            dispatch_order__batch__branch=user.branch
        )

    return get_object_or_404(
        queryset,
        pk=assignment_id,
    )


class DispatchBatchViewSet(
    ListModelMixin,
    RetrieveModelMixin,
    GenericViewSet,
):
    serializer_class = DispatchBatchSerializer
    permission_classes = [IsAuthenticated]

    queryset = (
        DispatchBatch.objects
        .select_related(
            "branch",
            "dispatcher",
            "created_by",
        )
        .prefetch_related(
            "orders__order",
            "orders__freight_assignments__freight_company",
            "orders__freight_assignments__created_by",
        )
        .all()
    )

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            return self.queryset

        return self.queryset.filter(
            branch=user.branch
        )


class DispatchOrderViewSet(
    ListModelMixin,
    RetrieveModelMixin,
    GenericViewSet,
):
    serializer_class = DispatchOrderSerializer
    permission_classes = [IsAuthenticated]

    queryset = (
        DispatchOrder.objects
        .select_related(
            "batch",
            "batch__branch",
            "batch__dispatcher",
            "order",
            "order__customer",
        )
        .prefetch_related(
            "freight_assignments__freight_company",
            "freight_assignments__created_by",
        )
        .all()
    )

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            return self.queryset

        return self.queryset.filter(
            batch__branch=user.branch
        )


class DispatchFreightAssignmentViewSet(
    ListModelMixin,
    RetrieveModelMixin,
    GenericViewSet,
):
    serializer_class = DispatchFreightAssignmentSerializer
    permission_classes = [IsAuthenticated]

    queryset = (
        DispatchFreightAssignment.objects
        .select_related(
            "dispatch_order",
            "dispatch_order__batch",
            "dispatch_order__batch__branch",
            "dispatch_order__order",
            "freight_company",
            "created_by",
        )
        .all()
    )

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            return self.queryset

        return self.queryset.filter(
            dispatch_order__batch__branch=user.branch
        )


class DispatchBatchCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DispatchBatchCreateSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        branch = get_object_or_404(
            Branch,
            pk=serializer.validated_data["branch"],
        )

        try:
            batch = create_dispatch_batch(
                branch=branch,
                created_by=request.user,
                scheduled_at=serializer.validated_data.get(
                    "scheduled_at"
                ),
                notes=serializer.validated_data.get(
                    "notes",
                    "",
                ),
            )
        except ValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            DispatchBatchSerializer(batch).data,
            status=status.HTTP_201_CREATED,
        )


class DispatchAddOrderAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, batch_id):
        batch = get_dispatch_batch_for_user(
            batch_id=batch_id,
            user=request.user,
        )

        serializer = DispatchOrderCreateSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        order = get_object_or_404(
            ShipmentOrder,
            pk=serializer.validated_data["order"],
        )

        try:
            dispatch_order = add_order_to_batch(
                batch=batch,
                order=order,
                added_by=request.user,
            )
        except ValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            DispatchOrderSerializer(dispatch_order).data,
            status=status.HTTP_201_CREATED,
        )


class DispatchRemoveOrderAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, dispatch_order_id):
        dispatch_order = get_dispatch_order_for_user(
            dispatch_order_id=dispatch_order_id,
            user=request.user,
        )

        try:
            remove_order_from_batch(
                dispatch_order=dispatch_order,
                removed_by=request.user,
            )
        except ValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "detail": "Order removed from dispatch batch."
            },
            status=status.HTTP_200_OK,
        )


class DispatchAssignFreightAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, dispatch_order_id):
        dispatch_order = get_dispatch_order_for_user(
            dispatch_order_id=dispatch_order_id,
            user=request.user,
        )

        serializer = DispatchFreightAssignmentCreateSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        freight_company = get_object_or_404(
            FreightCompany,
            pk=serializer.validated_data["freight_company"],
        )

        try:
            freight_amount = get_order_freight_amount(
                dispatch_order=dispatch_order,
            )

            assignment = assign_freight_company(
                dispatch_order=dispatch_order,
                freight_company=freight_company,
                payer=serializer.validated_data["payer"],
                created_by=request.user,
                freight_amount=freight_amount,
            )
        except ValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            DispatchFreightAssignmentSerializer(
                assignment
            ).data,
            status=status.HTTP_201_CREATED,
        )


class DispatchMakeReadyAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, batch_id):
        batch = get_dispatch_batch_for_user(
            batch_id=batch_id,
            user=request.user,
        )

        try:
            batch = make_batch_ready(
                batch=batch,
                changed_by=request.user,
            )
        except ValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            DispatchBatchSerializer(batch).data,
            status=status.HTTP_200_OK,
        )


class DispatchAssignDispatcherAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, batch_id):
        batch = get_dispatch_batch_for_user(
            batch_id=batch_id,
            user=request.user,
        )

        serializer = DispatchAssignDispatcherSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        try:
            batch = assign_dispatcher(
                batch=batch,
                dispatcher=serializer.validated_data[
                    "dispatcher"
                ],
                assigned_by=request.user,
            )
        except ValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            DispatchBatchSerializer(batch).data,
            status=status.HTTP_200_OK,
        )


class DispatchStartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, batch_id):
        batch = get_dispatch_batch_for_user(
            batch_id=batch_id,
            user=request.user,
        )

        try:
            batch = start_dispatch(
                batch=batch,
                started_by=request.user,
            )
        except ValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            DispatchBatchSerializer(batch).data,
            status=status.HTTP_200_OK,
        )


class DispatchDeliveredAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, dispatch_order_id):
        dispatch_order = get_dispatch_order_for_user(
            dispatch_order_id=dispatch_order_id,
            user=request.user,
        )

        serializer = DispatchDeliveredSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        try:
            assignment = (
                dispatch_order.freight_assignments
                .filter(
                    status=(
                        DispatchFreightAssignment
                        .Status
                        .DISPATCHING
                    )
                )
                .order_by("-assigned_at")
                .first()
            )

            if not assignment:
                raise ValidationError(
                    "No active freight assignment exists."
                )

            assignment = mark_freight_assignment_delivered(
                assignment=assignment,
                delivered_by=request.user,
                freight_invoice_number=(
                    serializer.validated_data[
                        "freight_invoice_number"
                    ]
                ),
                freight_invoice_file=(
                    serializer.validated_data.get(
                        "freight_invoice_file"
                    )
                ),
                notes=serializer.validated_data.get(
                    "notes",
                    "",
                ),
            )
        except ValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            DispatchFreightAssignmentSerializer(
                assignment
            ).data,
            status=status.HTTP_200_OK,
        )


class DispatchApproveAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, dispatch_order_id):
        dispatch_order = get_dispatch_order_for_user(
            dispatch_order_id=dispatch_order_id,
            user=request.user,
        )

        serializer = DispatchStatusSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        try:
            dispatch_order = approve_dispatch_handover(
                dispatch_order=dispatch_order,
                approved_by=request.user,
                notes=serializer.validated_data.get(
                    "notes",
                    "",
                ),
            )
        except ValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            DispatchOrderSerializer(dispatch_order).data,
            status=status.HTTP_200_OK,
        )


class DispatchRejectAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, dispatch_order_id):
        dispatch_order = get_dispatch_order_for_user(
            dispatch_order_id=dispatch_order_id,
            user=request.user,
        )

        serializer = DispatchRejectSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        try:
            dispatch_order = reject_dispatch_order(
                dispatch_order=dispatch_order,
                rejected_by=request.user,
                reason=serializer.validated_data["reason"],
                notes=serializer.validated_data.get(
                    "notes",
                    "",
                ),
            )
        except ValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            DispatchOrderSerializer(dispatch_order).data,
            status=status.HTTP_200_OK,
        )


class DispatchReturnAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, dispatch_order_id):
        dispatch_order = get_dispatch_order_for_user(
            dispatch_order_id=dispatch_order_id,
            user=request.user,
        )

        serializer = DispatchStatusSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        try:
            dispatch_order = return_dispatch_order(
                dispatch_order=dispatch_order,
                returned_by=request.user,
                notes=serializer.validated_data.get(
                    "notes",
                    "",
                ),
            )
        except ValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            DispatchOrderSerializer(dispatch_order).data,
            status=status.HTTP_200_OK,
        )


class DispatchCompleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, batch_id):
        batch = get_dispatch_batch_for_user(
            batch_id=batch_id,
            user=request.user,
        )

        try:
            batch = complete_dispatch_batch(
                batch=batch,
                completed_by=request.user,
            )
        except ValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            DispatchBatchSerializer(batch).data,
            status=status.HTTP_200_OK,
        )


class DispatchCancelBatchAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, batch_id):
        batch = get_dispatch_batch_for_user(
            batch_id=batch_id,
            user=request.user,
        )

        serializer = DispatchStatusSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        try:
            batch = cancel_dispatch_batch(
                batch=batch,
                cancelled_by=request.user,
                notes=serializer.validated_data.get(
                    "notes",
                    "",
                ),
            )
        except ValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            DispatchBatchSerializer(batch).data,
            status=status.HTTP_200_OK,
        )


class DispatchCancelOrderAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, dispatch_order_id):
        dispatch_order = get_dispatch_order_for_user(
            dispatch_order_id=dispatch_order_id,
            user=request.user,
        )

        serializer = DispatchStatusSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        try:
            dispatch_order = cancel_dispatch_order(
                dispatch_order=dispatch_order,
                cancelled_by=request.user,
                notes=serializer.validated_data.get(
                    "notes",
                    "",
                ),
            )
        except ValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            DispatchOrderSerializer(dispatch_order).data,
            status=status.HTTP_200_OK,
        )


class DispatchCancelAssignmentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, assignment_id):
        assignment = get_dispatch_assignment_for_user(
            assignment_id=assignment_id,
            user=request.user,
        )

        serializer = DispatchStatusSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        try:
            assignment = cancel_freight_assignment(
                assignment=assignment,
                cancelled_by=request.user,
                notes=serializer.validated_data.get(
                    "notes",
                    "",
                ),
            )
        except ValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            DispatchFreightAssignmentSerializer(
                assignment
            ).data,
            status=status.HTTP_200_OK,
        )