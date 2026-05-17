"""
Controller for Designation Approval workflows (SPV Admin).
Orchestrates CRUD operations and business logic.
"""
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.logger import logger
from ..crud.designation_approval import crud_designation_approval
from ..models.designation_approval import DesignationApproval
from ..services.notification_service import notification_service


class DesignationApprovalController:
    """
    Business logic for designation approval workflows.
    Coordinates between API layer and CRUD (database) layer.
    """

    async def list_approvals(
        self,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 10,
        search: Optional[str] = None,
        status_filter: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> Tuple[List[DesignationApproval], int]:
        """
        List designation approvals with pagination and filters.
        
        Returns:
            (items, total_count)
        """
        return await crud_designation_approval.list_designation_approvals(
            db=db,
            page=page,
            page_size=page_size,
            search=search,
            status_filter=status_filter,
            from_date=from_date,
            to_date=to_date,
        )

    async def approve(
        self,
        db: AsyncSession,
        record_id: uuid.UUID,
        approver_name: str,
        approver_id: str,
        background_tasks: BackgroundTasks,
    ) -> bool:
        """
        Approve a single designation approval request.
        
        Business Logic:
          1. Lock and fetch the PENDING record
          2. Validate state (PENDING only)
          3. Update status to APPROVED
          4. Commit transaction
          5. Send approval email notification (background)
        
        Returns:
            True if approved, False if not found or already processed
        """
        logger.info(f"Approving designation approval: {record_id}")
        success = await crud_designation_approval.approve(
            db=db,
            record_id=record_id,
        )
        
        if success:
            logger.info(f"Successfully approved designation approval: {record_id}")
            # Send email notification in background
            background_tasks.add_task(
                self._send_approval_email, record_id, approver_name, approver_id
            )
        else:
            logger.warning(f"Failed to approve designation approval: {record_id} (not found or already processed)")
        
        return success

    async def _send_approval_email(
        self,
        record_id: uuid.UUID,
        approver_name: str,
        approver_id: str,
    ) -> None:
        """Send approval email notification in background."""
        try:
            record = await crud_designation_approval.get_by_id(record_id)
            if not record or not record.user or not record.user.email:
                logger.warning(f"Cannot send approval email: record or user email not found for {record_id}")
                return

            approval_date = datetime.now(timezone.utc).strftime("%d %b %Y, %I:%M %p")
            await notification_service.send_designation_approved_email(
                to_email=record.user.email,
                designation_name=record.designation_name,
                approver_name=approver_name,
                approval_date=approval_date,
                user_id=approver_id,
            )
        except Exception:
            logger.exception(f"Error sending approval email for {record_id}")

    async def reject(
        self,
        db: AsyncSession,
        record_id: uuid.UUID,
        reviewer_comments: Optional[str] = None,
        rejector_name: str = "",
        rejector_id: str = "",
        background_tasks: BackgroundTasks = None,
    ) -> bool:
        """
        Reject a single designation approval request.
        
        Business Logic:
          1. Lock and fetch the PENDING record
          2. Validate state (PENDING only)
          3. Update status to REJECTED with comments
          4. Commit transaction
          5. Send rejection email notification (background)
        
        Args:
            db: Database session
            record_id: UUID of designation approval to reject
            reviewer_comments: Optional reason for rejection
            rejector_name: Name of the rejector from token
            rejector_id: User ID of the rejector from token
            background_tasks: FastAPI BackgroundTasks instance
        
        Returns:
            True if rejected, False if not found or already processed
        """
        logger.info(f"Rejecting designation approval: {record_id}")
        success = await crud_designation_approval.reject(
            db=db,
            record_id=record_id,
            reviewer_comments=reviewer_comments,
        )
        
        if success:
            logger.info(f"Successfully rejected designation approval: {record_id}")
            # Send email notification in background
            if background_tasks:
                background_tasks.add_task(
                    self._send_rejection_email, record_id, rejector_name, rejector_id, reviewer_comments
                )
        else:
            logger.warning(f"Failed to reject designation approval: {record_id} (not found or already processed)")
        
        return success

    async def _send_rejection_email(
        self,
        record_id: uuid.UUID,
        rejector_name: str,
        rejector_id: str,
        rejection_reason: Optional[str],
    ) -> None:
        """Send rejection email notification in background."""
        try:
            record = await crud_designation_approval.get_by_id(record_id)
            if not record or not record.user or not record.user.email:
                logger.warning(f"Cannot send rejection email: record or user email not found for {record_id}")
                return

            rejection_date = datetime.now(timezone.utc).strftime("%d %b %Y, %I:%M %p")
            await notification_service.send_designation_rejected_email(
                to_email=record.user.email,
                designation_name=record.designation_name,
                rejector_name=rejector_name,
                rejection_date=rejection_date,
                rejection_reason=rejection_reason if rejection_reason else "N/A",
                user_id=rejector_id,
            )
        except Exception:
            logger.exception(f"Error sending rejection email for {record_id}")


designation_approval_controller = DesignationApprovalController()
