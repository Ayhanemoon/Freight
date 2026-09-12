from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin

from freight.api.v1.serializers.collection_task import (
    CollectionTaskAssignSerializer,
    CollectionTaskSerializer,
    CollectionTaskStatusSerializer,
    CollectionTaskVerifyParcelSerializer,
)
from freight.models import CollectionTask
from freight.services.collection import (
    assign_collector,
    change_collection_status,
    complete_collection,
    verify_parcel,
)

def get_collection_task_for_user(task_id, user):
    queryset = CollectionTask.objects.select_related(
        "order",
        "order__branch",
        "order__customer",
        "collector",
    )

    if not user.is_superuser:
        queryset = queryset.filter(
            order__branch=user.branch
        )

    return get_object_or_404(
        queryset,
        pk=task_id,
    )

class CollectionTaskViewSet(
    ListModelMixin,
    RetrieveModelMixin,
    GenericViewSet,
):
    serializer_class = CollectionTaskSerializer
    permission_classes = [IsAuthenticated]

    queryset = (
        CollectionTask.objects
        .select_related(
            "order",
            "order__branch",
            "order__customer",
            "collector",
        )
        .prefetch_related(
            "order__parcels",
        )
        .all()
    )

    def get_queryset(self):
        user = self.request.user

        queryset = self.queryset

        if user.is_superuser:
            return queryset

        return queryset.filter(
            order__branch=user.branch
        )
    


class CollectionTaskAssignAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, task_id):
        task = get_collection_task_for_user(
            task_id=task_id,
            user=request.user,
        )

        serializer = CollectionTaskAssignSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        try:
            task = assign_collector(
                task=task,
                collector=serializer.validated_data["collector"],
            )
        except ValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            CollectionTaskSerializer(task).data,
            status=status.HTTP_200_OK,
        )


class CollectionTaskVerifyParcelAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, task_id):
        task = get_collection_task_for_user(
            task_id=task_id,
            user=request.user,
        )

        serializer = CollectionTaskVerifyParcelSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        try:
            parcel = verify_parcel(
                task=task,
                parcel=data["parcel"],
                verified_by=request.user,
                weight_kg=data["verified_weight_kg"],
                length_cm=data["verified_length_cm"],
                width_cm=data["verified_width_cm"],
                height_cm=data["verified_height_cm"],
            )
        except ValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "detail": "Parcel verified successfully.",
                "parcel_id": parcel.id,
                "verification_status": parcel.verification_status,
                "verified_by": parcel.verified_by_id,
                "verified_at": parcel.verified_at,
            },
            status=status.HTTP_200_OK,
        )


class CollectionTaskCompleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, task_id):
        task = get_collection_task_for_user(
            task_id=task_id,
            user=request.user,
        )

        try:
            task = complete_collection(
                task=task,
                completed_by=request.user,
            )
        except ValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            CollectionTaskSerializer(task).data,
            status=status.HTTP_200_OK,
        )


class CollectionTaskCancelAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, task_id):
        task = get_collection_task_for_user(
            task_id=task_id,
            user=request.user,
        )

        serializer = CollectionTaskStatusSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        try:
            task = change_collection_status(
                task=task,
                new_status=CollectionTask.Status.CANCELLED,
                user=request.user,
                note=serializer.validated_data.get("note", ""),
            )
        except ValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            CollectionTaskSerializer(task).data,
            status=status.HTTP_200_OK,
        )


class CollectionTaskFailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, task_id):
        task = get_collection_task_for_user(
            task_id=task_id,
            user=request.user,
        )

        serializer = CollectionTaskStatusSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        try:
            task = change_collection_status(
                task=task,
                new_status=CollectionTask.Status.FAILED,
                user=request.user,
                note=serializer.validated_data.get("note", ""),
            )
        except ValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            CollectionTaskSerializer(task).data,
            status=status.HTTP_200_OK,
        )