"""
Controller for Designation Approval workflows (SPV Admin).
Orchestrates CRUD operations and business logic.
"""
import uuid
from typing import List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.logger import logger
from ..crud.designation_approval import crud_designation_approval
from ..models.designation_approval import DesignationApproval


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
    ) -> bool:
        """
        Approve a single designation approval request.
        
        Business Logic:
          1. Lock and fetch the PENDING record
          2. Validate state (PENDING only)
          3. Update status to APPROVED
          4. Commit transaction
        
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
        else:
            logger.warning(f"Failed to approve designation approval: {record_id} (not found or already processed)")
        
        return success

    async def reject(
        self,
        db: AsyncSession,
        record_id: uuid.UUID,
        reviewer_comments: Optional[str] = None,
    ) -> bool:
        """
        Reject a single designation approval request.
        
        Business Logic:
          1. Lock and fetch the PENDING record
          2. Validate state (PENDING only)
          3. Update status to REJECTED with comments
          4. Commit transaction
        
        Args:
            db: Database session
            record_id: UUID of designation approval to reject
            reviewer_comments: Optional reason for rejection
        
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
        else:
            logger.warning(f"Failed to reject designation approval: {record_id} (not found or already processed)")
        
        return success


designation_approval_controller = DesignationApprovalController()
