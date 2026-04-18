export type PublicProfileInput = {
  userId: string;
  fullName?: string;
};

export function toPublicProfile(input: PublicProfileInput) {
  return {
    userId: input.userId,
    fullName: input.fullName ?? "",
    updatedAt: new Date(),
  };
}
