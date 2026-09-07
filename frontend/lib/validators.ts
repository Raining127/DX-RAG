const COLLECTION_NAME_PATTERN =
  /^[A-Za-z0-9][A-Za-z0-9_-]{1,48}[A-Za-z0-9]$/;

export const COLLECTION_NAME_REQUIREMENT =
  "名称须为 3–50 个字符，以字母或数字开头和结尾，中间仅可使用字母、数字、下划线或连字符";

export function validateCollectionName(name: string): string | null {
  return COLLECTION_NAME_PATTERN.test(name)
    ? null
    : COLLECTION_NAME_REQUIREMENT;
}
