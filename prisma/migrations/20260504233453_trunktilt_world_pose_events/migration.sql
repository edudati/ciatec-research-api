-- CreateTable
CREATE TABLE "trunktilt_world" (
    "id" TEXT NOT NULL,
    "match_id" TEXT NOT NULL,
    "timestamp_ms" BIGINT NOT NULL,
    "frame_id" INTEGER NOT NULL,
    "ball_pos_x" DOUBLE PRECISION NOT NULL,
    "ball_pos_y" DOUBLE PRECISION NOT NULL,
    "ball_pos_z" DOUBLE PRECISION NOT NULL,
    "ball_vel_x" DOUBLE PRECISION NOT NULL,
    "ball_vel_y" DOUBLE PRECISION NOT NULL,
    "ball_vel_z" DOUBLE PRECISION NOT NULL,
    "velocity_mag" DOUBLE PRECISION NOT NULL,
    "accel_mag" DOUBLE PRECISION NOT NULL,
    "tilt_x_x" DOUBLE PRECISION NOT NULL,
    "tilt_x_y" DOUBLE PRECISION NOT NULL,
    "tilt_x_z" DOUBLE PRECISION NOT NULL,
    "tilt_z_x" DOUBLE PRECISION NOT NULL,
    "tilt_z_y" DOUBLE PRECISION NOT NULL,
    "tilt_z_z" DOUBLE PRECISION NOT NULL,
    "input_virt_x" DOUBLE PRECISION NOT NULL,
    "input_virt_z" DOUBLE PRECISION NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "trunktilt_world_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "trunktilt_pose" (
    "id" TEXT NOT NULL,
    "match_id" TEXT NOT NULL,
    "timestamp_ms" BIGINT NOT NULL,
    "frame_id" INTEGER NOT NULL,
    "landmark_id" INTEGER NOT NULL,
    "x" DOUBLE PRECISION NOT NULL,
    "y" DOUBLE PRECISION NOT NULL,
    "z" DOUBLE PRECISION NOT NULL,
    "visibility" DOUBLE PRECISION,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "trunktilt_pose_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "trunktilt_events" (
    "id" TEXT NOT NULL,
    "match_id" TEXT NOT NULL,
    "type" TEXT NOT NULL,
    "timestamp" BIGINT NOT NULL,
    "data" JSONB NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "trunktilt_events_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "trunktilt_world_match_id_timestamp_ms_idx" ON "trunktilt_world"("match_id", "timestamp_ms");

-- CreateIndex
CREATE UNIQUE INDEX "trunktilt_world_match_id_frame_id_key" ON "trunktilt_world"("match_id", "frame_id");

-- CreateIndex
CREATE INDEX "trunktilt_pose_match_id_landmark_id_timestamp_ms_idx" ON "trunktilt_pose"("match_id", "landmark_id", "timestamp_ms");

-- CreateIndex
CREATE INDEX "trunktilt_pose_match_id_frame_id_idx" ON "trunktilt_pose"("match_id", "frame_id");

-- CreateIndex
CREATE UNIQUE INDEX "trunktilt_pose_match_id_frame_id_landmark_id_key" ON "trunktilt_pose"("match_id", "frame_id", "landmark_id");

-- CreateIndex
CREATE INDEX "trunktilt_events_match_id_timestamp_idx" ON "trunktilt_events"("match_id", "timestamp");

-- AddForeignKey
ALTER TABLE "trunktilt_world" ADD CONSTRAINT "trunktilt_world_match_id_fkey" FOREIGN KEY ("match_id") REFERENCES "matches"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "trunktilt_pose" ADD CONSTRAINT "trunktilt_pose_match_id_fkey" FOREIGN KEY ("match_id") REFERENCES "matches"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "trunktilt_events" ADD CONSTRAINT "trunktilt_events_match_id_fkey" FOREIGN KEY ("match_id") REFERENCES "matches"("id") ON DELETE CASCADE ON UPDATE CASCADE;
